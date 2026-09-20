# -*- coding: utf-8 -*-
"""Cross-dataset table, datasets as rows, one column per fit variable, with the
recorded temperature range and a citation per dataset."""
import numpy as np, pandas as pd

df = pd.concat([pd.read_csv('scratchpad/cross_table.csv'),
                pd.read_csv('scratchpad/neea_rows.csv')], ignore_index=True).set_index('label')

ROW = {  # label -> "location ~cite"
    'German WPuQ (real HP)':               r'Hamelin, DE~\cite{Sch22}',
    'Swiss substation (real HP)':          r'Kloten, CH~\cite{Bru25,Kai26b}',
    'Austin Pecan St (real)':              r'Austin, US~\cite{pecanstreet}',
    'NEEA WA (real HP)':                   r'Washington, US~\cite{neea_eulr}',
    'NEEA OR (real HP)':                   r'Oregon, US~\cite{neea_eulr}',
    'ResStock ASHP -- Hennepin MN (cold)': r'Hennepin, US~\cite{resstock}',
    'ResStock ASHP -- King WA (mild)':     r'King, US~\cite{resstock}',
    'ResStock ASHP -- Maricopa AZ (hot)':  r'Maricopa, US~\cite{resstock}',
}
order = [k for k in ROW if k in df.index]

COLS = [('$n$', 'n', '.0f'), (r'$T_{\min}$', 'T_min', '.0f'), (r'$T_{\max}$', 'T_max', '.0f'),
        (r'$P_{\mathrm{base}}$', 'P_base', '.0f'), ('$s_h$', 's_h', '.1f'), ('$T_h$', 'T_h', '.1f'),
        ('$s_c$', 's_c', '.1f'), ('$T_c$', 'T_c', '.1f'), ('$R^2$', 'R2', '.2f'),
        ('$b_h$', 'b_h', '.3f'), ('$m_h$', 'm_h', '.3f'), (r'SF$_\mathrm{c}$', 'SF_cold', '.2f'), ('$R^2_h$', 'R2_SFh', '.2f'),
        ('$b_c$', 'b_c', '.3f'), ('$m_c$', 'm_c', '.3f'), (r'SF$_\mathrm{h}$', 'SF_hot', '.2f'), ('$R^2_c$', 'R2_SFc', '.2f')]

def cell(v, fmt):
    return '--' if (v is None or (isinstance(v, float) and not np.isfinite(v))) else format(v, fmt)

body = '\n'.join(ROW[lab] + ' & ' + ' & '.join(cell(df.loc[lab, c], f) for _, c, f in COLS) + r' \\'
                for lab in order)
head2 = 'dataset & ' + ' & '.join(h for h, _, _ in COLS) + r' \\'

tex = (
    r"\begin{table*}[t]" "\n" r"\centering" "\n"
    r"\caption{Net-load and SF fit parameters for one aggregate per dataset (ResStock rows are the ASHP-electrification scenario; a single hockey stick is used where only one arm is present). $n$ is the number of aggregated consumers; $T_{\min},T_{\max}$ the recorded temperature range [$^\circ$C]; $s_h,s_c$ [kW/$^\circ$C]; $T_h,T_c$ [$^\circ$C]; $m_h,m_c$ [$^\circ$C$^{-1}$]; SF$_\mathrm{c}$/SF$_\mathrm{h}$ the coldest-/hottest-day SF.}" "\n"
    r"\label{tab:cross}" "\n" r"\scriptsize\setlength{\tabcolsep}{2.6pt}" "\n"
    r"\begin{tabular}{l" + "c" * len(COLS) + "}\n" r"\toprule" "\n"
    r" & \multicolumn{3}{c}{} & \multicolumn{6}{c}{Net-load fit $\hat{P}_{\mathrm{net}}(T)$} & \multicolumn{8}{c}{SF fit $\hat{\mathrm{SF}}(T)$}\\" "\n"
    r"\cmidrule(lr){5-10}\cmidrule(lr){11-18}" "\n"
    + head2 + "\n" r"\midrule" "\n" + body + "\n" r"\bottomrule" "\n"
    r"\end{tabular}" "\n" r"\end{table*}" "\n")

open('paper/tables/tab_cross.tex', 'w').write(tex)
print(tex)
print('wrote paper/tables/tab_cross.tex')
