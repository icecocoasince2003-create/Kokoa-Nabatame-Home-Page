/* =========================================================
   夜空の背景
   ・星空が北の空を中心に、ゆっくり回ります
   ・星がまたたき、ときどき流れ星が流れます
   ・金色の小さな星は、エジプトの墓の天井画の星をかたどったものです
   ・ページを移動しても、同じ星空がそのまま続きます
   ・端末で「動きを減らす」設定にしている人には、止まった星空を表示します

   ふだんは触らなくてOK。変えたいときは下の「調整できる値」だけ。
   ========================================================= */
(() => {
    "use strict";

    // ---------- 調整できる値 ----------
    const STAR_DENSITY = 0.00034;    // 星の多さ（大きくすると増える）
    const ROTATION_SPEED = 0.005;    // 星空が回る速さ（0 で止まる）
    const METEORS = true;            // 流れ星を出すか（false で出ない）
    const METEOR_INTERVAL = [6, 15]; // 流れ星の間隔（秒）
    const GOLD_RATIO = 0.07;         // 金色の星の割合
    const EGYPTIAN_STARS = 4;        // 天井画ふうの金の星（1画面あたりの数。0 で消える）
    const MILKY_WAY = true;          // 天の川を出すか
    // ----------------------------------

    const canvas = document.getElementById("sky");
    if (!canvas || !canvas.getContext) return;
    const ctx = canvas.getContext("2d");
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const COLORS = ["#ffffff", "#e4ecff", "#cbd9ff", "#f2d9a2"]; // 最後が金色
    let W = 0, H = 0, dpr = 1;
    let pole = { x: 0, y: 0 };
    let stars = [], sbas = [];
    let band = null; // 天の川のぼんやりした光（最初に一度だけ描いておく）
    let meteor = null, nextMeteor = 0, lastFrame = 0, parallax = 0;

    // ページを移動しても星空が続くように、回り始めた時刻を覚えておく
    let start = Date.now();
    try {
        const saved = Number(sessionStorage.getItem("sky-start"));
        if (saved && start - saved < 6 * 3600 * 1000) start = saved;
        else sessionStorage.setItem("sky-start", String(start));
    } catch (e) {
        /* 保存できない環境でもそのまま動く */
    }
    const now = () => (Date.now() - start) / 1000;

    // 毎回同じ星空になるよう、決まった並びの乱数を使う
    let seed = 0;
    const rnd = () => {
        seed = (seed + 0x6d2b79f5) | 0;
        let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    const range = (a, b, r = rnd) => a + r() * (b - a);
    const gauss = () => Math.sqrt(-2 * Math.log(1 - rnd())) * Math.cos(2 * Math.PI * rnd());
    const rgba = (hex, a) => {
        const n = parseInt(hex.slice(1), 16);
        return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`;
    };

    // ---------- 星の絵（最初に一度だけ作る） ----------
    function sprite(size, paint) {
        const c = document.createElement("canvas");
        c.width = c.height = size;
        paint(c.getContext("2d"), size);
        return c;
    }

    const starSprites = COLORS.map((col) =>
        sprite(32, (g, s) => {
            const r = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
            r.addColorStop(0, col);
            r.addColorStop(0.16, col);
            r.addColorStop(0.3, rgba(col, 0.3));
            r.addColorStop(1, rgba(col, 0));
            g.fillStyle = r;
            g.fillRect(0, 0, s, s);
        })
    );

    const glowSprite = sprite(128, (g, s) => {
        const r = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
        r.addColorStop(0, "rgba(165,185,255,1)");
        r.addColorStop(0.45, "rgba(165,185,255,0.4)");
        r.addColorStop(1, "rgba(165,185,255,0)");
        g.fillStyle = r;
        g.fillRect(0, 0, s, s);
    });

    // エジプトの天井画の星（中心から5本の腕がのびる形）
    const sbaSprite = sprite(48, (g, s) => {
        g.translate(s / 2, s / 2);
        g.strokeStyle = "#e6c587";
        g.lineWidth = 3.4;
        g.lineCap = "round";
        for (let i = 0; i < 5; i++) {
            const a = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
            g.beginPath();
            g.moveTo(0, 0);
            g.lineTo(Math.cos(a) * 19, Math.sin(a) * 19);
            g.stroke();
        }
    });

    // ---------- 星空を作る ----------
    function makeStar(x, y, inBand) {
        const big = rnd() < (inBand ? 0.015 : 0.05);
        const gold = rnd() < GOLD_RATIO;
        return {
            x,
            y,
            big,
            r: big ? range(1.3, 2.3) : range(0.6, 1.3) * (inBand ? 0.8 : 1),
            a: big ? range(0.7, 1) : (inBand ? 0.14 + rnd() ** 2 * 0.5 : 0.18 + rnd() ** 2 * 0.72),
            c: gold ? 3 : Math.floor(rnd() * 3),
            tw: rnd() < 0.6 ? range(0.2, 0.65) : 0, // またたきの強さ
            f: range(0.5, 2.2), // またたきの速さ
            ph: range(0, Math.PI * 2),
        };
    }

    function generate() {
        seed = 7741; // 何回作っても同じ星空になる
        pole = { x: W * 0.8, y: -H * 0.22 }; // 回転の中心（画面の右上の外）
        const corners = [[0, 0], [W, 0], [0, H], [W, H]];
        const rMax = Math.max(...corners.map(([x, y]) => Math.hypot(x - pole.x, y - pole.y))) + 260;
        const disk = Math.PI * rMax * rMax;
        const polar = () => {
            const r = rMax * Math.sqrt(rnd());
            const t = rnd() * Math.PI * 2;
            return [r * Math.cos(t), r * Math.sin(t)];
        };

        stars = [];
        const n = Math.round(STAR_DENSITY * disk);
        for (let i = 0; i < n; i++) stars.push(makeStar(...polar(), false));

        // 天の川：画面の中ほどを斜めに横切る、星の多い帯
        band = null;
        if (MILKY_WAY) {
            const cx = W * 0.4 - pole.x, cy = H * 0.55 - pole.y, ang = -0.42;
            const dx = Math.cos(ang), dy = Math.sin(ang);
            const len = rMax * 1.6;
            const m = Math.round(n * 0.45);
            for (let i = 0; i < m; i++) {
                const u = range(-len / 2, len / 2), v = gauss() * 70;
                stars.push(makeStar(cx + u * dx - v * dy, cy + u * dy + v * dx, true));
            }
            // ぼんやりした光は小さく描いておき、表示するときに引き伸ばす（軽くするため）
            const S = 0.25, GAIN = 6;
            const gw = len + 600, gh = 360;
            const layer = sprite(1, () => {});
            layer.width = Math.ceil(gw * S);
            layer.height = Math.ceil(gh * S);
            const g = layer.getContext("2d");
            g.scale(S, S);
            g.translate(gw / 2, gh / 2);
            for (let u = -len / 2; u < len / 2; u += 150) {
                const v = gauss() * 25, w = range(380, 560), h = range(130, 210);
                g.globalAlpha = range(0.03, 0.055) * GAIN;
                g.drawImage(glowSprite, u - w / 2, v - h / 2, w, h);
            }
            band = { layer, cx, cy, ang, gw, gh, alpha: 1 / GAIN };
        }

        sbas = [];
        const k = Math.round((EGYPTIAN_STARS * disk) / (W * H));
        for (let i = 0; i < k; i++) {
            const [x, y] = polar();
            sbas.push({ x, y, size: range(8, 11), a: range(0.5, 0.8), rot: range(0, Math.PI * 2), f: range(0.4, 1), ph: range(0, Math.PI * 2) });
        }

        stars.sort((p, q) => p.c - q.c); // 色ごとにまとめて描くと速い
    }

    // ---------- 描く ----------
    function draw(T) {
        const th = T * ROTATION_SPEED;
        const c = Math.cos(th), s = Math.sin(th);
        const px = pole.x, py = pole.y - parallax;
        const outside = (x, y, m) => x < -m || y < -m || x > W + m || y > H + m;

        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, W, H);

        if (band) {
            ctx.save();
            ctx.translate(px, py);
            ctx.rotate(th);
            ctx.translate(band.cx, band.cy);
            ctx.rotate(band.ang);
            ctx.globalAlpha = band.alpha;
            ctx.drawImage(band.layer, -band.gw / 2, -band.gh / 2, band.gw, band.gh);
            ctx.restore();
        }

        let col = -1;
        for (const st of stars) {
            const x = px + st.x * c - st.y * s, y = py + st.x * s + st.y * c;
            if (outside(x, y, 8)) continue;
            let a = st.a;
            if (st.tw && !still) a *= 1 - st.tw * (0.5 + 0.5 * Math.sin(T * st.f + st.ph));
            ctx.globalAlpha = a;
            if (st.big) {
                const d = st.r * 7;
                ctx.drawImage(starSprites[st.c], x - d / 2, y - d / 2, d, d);
            } else {
                if (st.c !== col) {
                    col = st.c;
                    ctx.fillStyle = COLORS[col];
                }
                ctx.fillRect(x - st.r / 2, y - st.r / 2, st.r, st.r);
            }
        }

        for (const e of sbas) {
            const x = px + e.x * c - e.y * s, y = py + e.x * s + e.y * c;
            if (outside(x, y, 20)) continue;
            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(e.rot + th);
            ctx.globalAlpha = still ? e.a : e.a * (0.75 + 0.25 * Math.sin(T * e.f + e.ph));
            ctx.drawImage(sbaSprite, -e.size / 2, -e.size / 2, e.size, e.size);
            ctx.restore();
        }

        if (meteor) drawMeteor(T);
        ctx.globalAlpha = 1;
    }

    // ---------- 流れ星 ----------
    function spawnMeteor(T) {
        const ang = range(0.3, 0.6, Math.random); // 水平から少し下向き
        meteor = {
            t0: T,
            life: range(0.7, 1.1, Math.random),
            x: range(W * 0.3, W * 1.05, Math.random),
            y: range(-H * 0.05, H * 0.35, Math.random),
            dx: -Math.cos(ang),
            dy: Math.sin(ang),
            v: range(650, 950, Math.random),
            len: range(110, 190, Math.random),
        };
    }

    function drawMeteor(T) {
        const m = meteor, age = T - m.t0;
        if (age > m.life || age < 0) {
            meteor = null;
            nextMeteor = T + range(METEOR_INTERVAL[0], METEOR_INTERVAL[1], Math.random);
            return;
        }
        const k = age / m.life;
        const hx = m.x + m.dx * m.v * age, hy = m.y + m.dy * m.v * age;
        const L = m.len * Math.min(1, k * 3);
        const tx = hx - m.dx * L, ty = hy - m.dy * L;
        const a = Math.sin(Math.PI * k);
        const g = ctx.createLinearGradient(hx, hy, tx, ty);
        g.addColorStop(0, `rgba(255,248,232,${a})`);
        g.addColorStop(1, "rgba(255,248,232,0)");
        ctx.globalAlpha = 1;
        ctx.strokeStyle = g;
        ctx.lineWidth = 1.6;
        ctx.lineCap = "round";
        ctx.beginPath();
        ctx.moveTo(hx, hy);
        ctx.lineTo(tx, ty);
        ctx.stroke();
        ctx.globalAlpha = a;
        ctx.drawImage(starSprites[0], hx - 5, hy - 5, 10, 10);
    }

    // ---------- 動かす ----------
    function frame(ts) {
        requestAnimationFrame(frame);
        if (!meteor && ts - lastFrame < 33) return; // ふだんは1秒30コマで十分（電池にやさしい）
        lastFrame = ts;
        const T = now();
        if (METEORS && !meteor && T > nextMeteor) spawnMeteor(T);
        draw(T);
    }

    function resize() {
        const w = canvas.clientWidth, h = canvas.clientHeight;
        const ratio = Math.min(window.devicePixelRatio || 1, 2);
        if (w === W && h === H && ratio === dpr) return;
        const regenerate = !stars.length || Math.abs(w - W) > 1 || h > H + 200;
        W = w;
        H = h;
        dpr = ratio;
        canvas.width = Math.round(W * dpr);
        canvas.height = Math.round(H * dpr);
        if (regenerate) generate();
        draw(still ? 0 : now());
    }

    window.addEventListener("resize", resize);
    resize();

    if (!still) {
        // スクロールすると星空が少しだけずれて、奥行きが出る
        window.addEventListener("scroll", () => {
            parallax = Math.min(window.scrollY * 0.06, 240);
        }, { passive: true });
        nextMeteor = now() + range(2.5, 5, Math.random);
        requestAnimationFrame(frame);
    }
})();
