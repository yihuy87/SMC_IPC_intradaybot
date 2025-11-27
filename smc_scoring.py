# smc_scoring.py

"""
SMC IPC Scoring v2 — Intraday 5m (ketat, fokus akurasi)

Fokus:
- Bias 1H searah (strong bullish)
- Struktur 15m bullish
- Discount zone IPC (ipc_discount_core + ipc_deep_discount)
- IPC block utama (Mitigation / Breaker), FVG sebagai confluence
- Trigger CHoCH (ipc_trigger_core), pre-pump sebagai pendukung
- Liquidity event utama: sweep (ipc_liquidity_core) + target likuiditas
- Hanya dipakai untuk menilai setup yang sudah lolos smc_logic IPC
"""

def score_smc_signal(c: dict) -> int:
    """
    Scoring SMC IPC (0–160 an)
    """
    score = 0

    # ============================================================
    # 1. HIGHER TIMEFRAME (1H + 15m)
    # ============================================================
    # Strong bullish bias 1H lebih besar poinnya
    if c.get("bias_1h_strong_bullish"):
        score += 20
    elif c.get("bias_1h_not_bearish"):
        score += 10

    if c.get("struct_15m_bullish"):
        score += 15  # struktur intraday naik

    # ============================================================
    # 2. TRIGGER (CHoCH / Pre-pump)
    # ============================================================
    # IPC trigger utama: CHoCH impuls
    if c.get("ipc_trigger_core") or c.get("has_choch_impulse"):
        score += 22

    # Pre-pump context = pendukung trigger (kompresi sebelum impuls)
    if c.get("ipc_trigger_support") or c.get("has_pre_pump_context"):
        score += 5

    # ============================================================
    # 3. DISCOUNT ZONE (IPC)
    # ============================================================
    # ipc_discount_core: deep discount ATAU moderate+block
    if c.get("ipc_discount_core"):
        score += 15

    # Deep discount = ekstra poin
    if c.get("ipc_deep_discount") or c.get("in_discount_62_79"):
        score += 8
    else:
        # Kalau cuma di 50–62 (moderate) dapat sedikit poin ekstra
        if c.get("in_discount_50_62"):
            score += 4

    # ============================================================
    # 4. IPC BLOCK (MB / Breaker / FVG)
    # ============================================================
    # IPC block core = Mitigation / Breaker (wajib di logic)
    if c.get("ipc_block_core"):
        score += 18

    # Detail block
    if c.get("has_mitigation_block"):
        score += 4

    if c.get("has_breaker_block"):
        score += 4

    # FVG = imbalance sebagai confluence, bukan syarat wajib
    if c.get("has_fvg_fresh"):
        score += 6

    # synergy block + FVG
    if (c.get("ipc_block_core") or c.get("ipc_block_any")) and c.get("has_fvg_fresh"):
        score += 3

    # ============================================================
    # 5. LIQUIDITY (Sweep + Target)
    # ============================================================
    # Liquidity event utama: sweep di 5m
    if c.get("ipc_liquidity_core") or c.get("has_big_sweep"):
        score += 15

    # Liquidity target cluster 15m sebagai pendukung
    if c.get("ipc_liquidity_support") or c.get("liquidity_target_clear"):
        score += 5

    # ============================================================
    # 6. QUALITY / CONTEXT BONUS
    # ============================================================
    # Momentum & kondisi market (logikanya sudah di-filter di smc_logic,
    # tapi kalau mau dipakai di tempat lain tetap aman)
    if c.get("momentum_ok"):
        score += 5

    if c.get("not_fake_pump"):
        score += 3

    if c.get("not_choppy"):
        score += 3

    # Placeholder: kalau di future kamu isi real divergence / exhaustion
    if c.get("no_bearish_divergence"):
        score += 2
    if c.get("no_exhaustion_sign"):
        score += 2

    # ============================================================
    # 7. SYNERGY BONUS: IPC chain lengkap
    # ============================================================
    ipc_valid = c.get("ipc_valid_setup")

    # chain inti IPC: bias + struktur + discount + block + trigger + liquidity
    bias_ok   = c.get("bias_1h_strong_bullish") or c.get("bias_1h_not_bearish")
    struct    = c.get("struct_15m_bullish")
    disc_core = c.get("ipc_discount_core")
    block_core = c.get("ipc_block_core")
    trig_core = c.get("ipc_trigger_core") or c.get("has_choch_impulse")
    liq_core  = c.get("ipc_liquidity_core") or c.get("has_big_sweep")

    if ipc_valid and bias_ok and struct and disc_core and block_core and trig_core and liq_core:
        # setup bener-bener lengkap sesuai rule IPC ketat
        score += 8

    # bonus kecil kalau deep discount + block core + FVG → confluence area entry sangat kuat
    if (c.get("ipc_deep_discount") or c.get("in_discount_62_79")) and block_core and c.get("has_fvg_fresh"):
        score += 7

    return score


def tier_from_score(score: int) -> str:
    """
    Mapping score → Tier (disesuaikan dengan skala IPC baru)
    - A+ : >= 130
    - A  : 110–129
    - B  : 90–109
    - NONE : < 90
    """
    if score >= 130:
        return "A+"
    elif score >= 110:
        return "A"
    elif score >= 90:
        return "B"
    else:
        return "NONE"


def should_send_tier(tier: str, min_tier: str) -> bool:
    """
    Bandingkan tier terhadap min_tier:
    Urutan: NONE < B < A < A+
    Default min_tier umumnya "A" kalau mau fokus winrate tinggi.
    """
    order = {"NONE": 0, "B": 1, "A": 2, "A+": 3}
    return order.get(tier, 0) >= order.get(min_tier, 2)
