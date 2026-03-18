st.markdown(f"""
<div style='display:flex; gap:12px; margin-bottom:16px;'>
    <div class="metric-card" style='flex:1; padding:20px 0;'>
        <div class="metric-label">TOTAL (총 자산)</div>
        <div class="metric-value">{fmt(curr['총자산'])}</div>
        {pct_html(pct_change('총자산'))}
        {delta_html(curr['총자산']-prev['총자산'])}
    </div>
    <div class="metric-card" style='flex:1; padding:20px 0;'>
        <div class="metric-label">김프차익 (업비트&바이비트)</div>
        <div class="metric-value">{fmt(curr['김프차익'])}</div>
        {pct_html(pct_change('김프차익'))}
        {delta_html(curr['김프차익']-prev['김프차익'])}
    </div>
    <div class="metric-card" style='flex:1; padding:20px 0;'>
        <div class="metric-label">OKX (시그널봇&현물)</div>
        <div class="metric-value">{fmt(curr['OKX통합'])}</div>
        {pct_html(pct_change('OKX통합'))}
        {delta_html(curr['OKX통합']-prev['OKX통합'])}
    </div>
    <div class="alloc-card" style='flex:1; padding:20px 18px;'>
        <div class="alloc-label">자산 비중</div>
        <div class="alloc-row">
            <div class="alloc-dot" style="background:#00E676;"></div>
            <div class="alloc-name">KIMP</div>
            <div class="alloc-bar-bg"><div class="alloc-bar-fill" style="width:{kimp_ratio:.1f}%;background:#00E676;"></div></div>
            <div class="alloc-pct">{kimp_ratio:.1f}%</div>
        </div>
        <div class="alloc-row">
            <div class="alloc-dot" style="background:#3B82F6;"></div>
            <div class="alloc-name">OKX</div>
            <div class="alloc-bar-bg"><div class="alloc-bar-fill" style="width:{okx_ratio:.1f}%;background:#3B82F6;"></div></div>
            <div class="alloc-pct">{okx_ratio:.1f}%</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
