# -*- coding: utf-8 -*-
"""Assemble hp_sensitivity_v6.tex from v4 in the new 8-section structure:
 I Introduction | II Problem Statement and Approach (v4 II+III) |
 III Installed Capacity Estimation (v4 IV-A) | IV Flexibility Quantification (v4 IV-C) |
 V Numerical Results (v4 V-A,B,C,D,F) | VI Validation | VII Discussion | VIII Conclusion.
Energy (v4 IV-B and V-E) is dropped. Prose is relocated verbatim; headers, a few
role-naming cross-refs, and the energy scrubs are handled here / as follow-up edits.
Carries the Nomenclature and an energy-free pipeline diagram."""
import re

src = open('paper/hp_sensitivity_v4.tex', encoding='utf-8').read().split('\n')
start = next(i for i, l in enumerate(src) if l.startswith(r'\section{Introduction}'))
preamble = src[:start]

bnds = [i for i in range(start, len(src))
        if src[i].startswith(r'\section{') or src[i].startswith(r'\subsection{')]
bnds.append(len(src))
blocks = []
for a, b in zip(bnds[:-1], bnds[1:]):
    chunk = src[a:b]
    while chunk and (chunk[-1].strip() == '' or chunk[-1].startswith('% ===')):
        chunk.pop()
    m = re.search(r'\\label\{(sec:[^}]+)\}', '\n'.join(chunk[:3]))
    key = m.group(1) if m else ('disc:' + chunk[0])
    blocks.append([chunk[0], key, chunk])
B = {k: lines for (_h, k, lines) in blocks}

def after_header(lines):
    return lines[2:] if len(lines) > 1 and re.match(r'\\label', lines[1]) else lines[1:]
def edit(lines, old, new):
    return '\n'.join(lines).replace(old, new).split('\n')

# --- header renames / promotions / in-block cross-ref fixes -------------------
B['sec:problem'][0] = r'\section{Problem Statement and Approach}'
# make sec:fits resolve to this merged section
for i, l in enumerate(B['sec:problem'][:3]):
    if l.strip() == r'\label{sec:problem}':
        B['sec:problem'].insert(i + 1, r'\label{sec:fits}')
        break

B['sec:fits-sf'] = edit(B['sec:fits-sf'],
    r'Section~\ref{sec:usecases} combines them,', r'Section~\ref{sec:uc-capacity} combines them,')

cap = list(B['sec:uc-capacity'])
cap[0] = r'\section{Installed Capacity Estimation}'
cap = edit(cap, r'tested in Sections~\ref{sec:results} and \ref{sec:validation}.',
           r'tested in Section~\ref{sec:results}.')
B['sec:uc-capacity'] = cap

flx = list(B['sec:uc-flex'])
flx[0] = r'\section{Flexibility Quantification}'
B['sec:uc-flex'] = flx

B['sec:validation'][0] = r'\section{Validation on an Unseen Feeder}'

fits_intro = after_header(B['sec:fits'])   # the "Two functions are defined..." paragraph

# --- new literal content ------------------------------------------------------
nomen = r"""% =====================================================================
\section*{Nomenclature}
\begin{IEEEdescription}[\IEEEsetlabelwidth{$P_{\text{non-ETL}}(t)$}]
\item[$P_{\mathrm{net}}(t)$] Aggregated net load.
\item[$P_{\mathrm{ETL}}(t)$] Aggregated ETL (heat-pump) load.
\item[$P_{\text{non-ETL}}(t)$] Aggregated non-ETL load.
\item[$P_{\mathrm{base}}$] Temperature-independent base load.
\item[$s_h,\ s_c$] Heating, cooling sensitivities [kW/$^\circ$C].
\item[$T_h,\ T_c$] Heating, cooling threshold temperatures [$^\circ$C].
\item[$P_{\mathrm{ETL}}^{\max}$] ETL installed capacity.
\item[$\mathrm{SF}(T)$] Simultaneity factor.
\item[$b,\ m$] SF base fraction, sensitivity [1/$^\circ$C].
\item[$T_h^{\mathrm{SF}}$] SF threshold temperature [$^\circ$C].
\item[$T_{\min}$] Coldest recorded temperature [$^\circ$C].
\item[$\alpha_F$] Flexibility duty cycle.
\item[$\Delta t_{Th}$] Thermal-inertia window [h].
\item[$E_{\mathrm{flex}}$] Flexible energy [kWh].
\item[$N,\ N_{hp}$] Consumers, HPs behind the meter.
\end{IEEEdescription}"""

pipeline = r"""\begin{figure}[t]
\centering
\resizebox{\columnwidth}{!}{%
\begin{tikzpicture}[font=\scriptsize, >=latex,
  io/.style={draw, fill=black!6, rounded corners=1pt, align=center, text width=13.5mm, minimum height=6.5mm, inner sep=1.5pt},
  proc/.style={draw, rounded corners=3pt, align=center, text width=13.5mm, minimum height=6.5mm, inner sep=1.5pt},
  node distance=6mm and 8mm]
\node[io] (net) {Aggregated net load};
\node[io, above=of net] (sub) {Submetered ETL pilot};
\node[io, below=of net] (temp) {Ambient temperature};
\node[proc, right=of net] (bath) {Net-load fit Eq.~\eqref{eq:bathtub}};
\node[proc, right=of sub] (sf) {SF fit Eq.~\eqref{eq:sffit}};
\node[proc, right=14mm of sf] (cap) {Installed cap. Eq.~\eqref{eq:capacity}};
\node[proc, right=of cap] (fl) {Flexibility Eq.~\eqref{eq:flex-energy}};
\draw[->] (sub) -- (sf);
\draw[->] (net) -- (bath);
\draw[->] (temp) -| (bath);
\draw[->] (sf) -- (cap) node[midway, above, font=\tiny] {transferred};
\draw[->] (bath) -- (cap.south west);
\draw[->] (cap) -- (fl);
\draw[->] (sf.north) -- ([yshift=6mm]sf.north) -| (fl.north);
\end{tikzpicture}%
}
\caption{Method pipeline. The observable net-load fit and a submetered-pilot SF fit combine into the installed capacity; the capacity with the SF gives the flexibility. The transferred SF also shapes the flexibility.}
\label{fig:pipeline}
\end{figure}"""

# --- emit ---------------------------------------------------------------------
out = list(preamble)
for i, l in enumerate(out):
    if l.startswith(r'\usepackage{graphicx}'):
        out.insert(i + 1, r'\usepackage{tikz}')
        out.insert(i + 2, r'\usetikzlibrary{positioning,arrows.meta}')
        break
# nomenclature after keywords
for i, l in enumerate(out):
    if l.startswith(r'\end{IEEEkeywords}'):
        out[i] = l + '\n\n' + nomen
        break

def sec(lines):
    out.append(''); out.append('% ' + '=' * 69); out.extend(lines)
def sub(lines):
    out.append(''); out.extend(lines)

sec(B['sec:intro'])
sec(B['sec:problem'])
sub(pipeline.split('\n'))
sub(fits_intro)
sub(B['sec:fits-net'])
sub(B['sec:fits-sf'])
sec(B['sec:uc-capacity'])
sec(B['sec:uc-flex'])
sec(B['sec:results'])
sub(B['sec:data'])
sub(B['sec:res-ff'])
sub(B['sec:res-sf'])
sub(B['sec:res-capacity'])
sub(B['sec:res-flex'])
sec(B['sec:validation'])
sec(B['sec:discussion'])
for _h, k, lines in blocks:
    if _h.startswith(r'\subsection') and k.startswith('disc:') and any(
        t in _h for t in ['Accuracy', 'Generalisation', 'Data Requirements', 'Limitations', 'Concluding']):
        sub(lines)
sec(B['sec:conclusion'])
out.append('')

open('paper/hp_sensitivity_v6.tex', 'w', encoding='utf-8').write('\n'.join(out))

# integrity: dropped-energy prose must be gone; everything else present
def prose(text):
    return [l.strip() for l in text if l.strip() and not l.strip().startswith('%')
            and not l.strip().startswith(r'\section') and not l.strip().startswith(r'\subsection')]
srcset, outset = prose(src[start:]), prose(out)
dropped = [k for k in ('sec:usecases', 'sec:uc-energy', 'sec:res-energy')]
print('v6 written,', len(out), 'lines')
print('dropped blocks present in v6? ',
      {k: any(x in '\n'.join(out) for x in prose(B[k])[:1]) for k in dropped})
missing = [l for l in srcset if l not in outset]
print(f'non-dropped source lines missing from v6: '
      f'{len([l for l in missing if l not in sum([prose(B[k]) for k in dropped], [])])}')
