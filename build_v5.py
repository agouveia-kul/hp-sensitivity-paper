# -*- coding: utf-8 -*-
"""Assemble hp_sensitivity_v5.tex by RELOCATING whole content blocks of v4 into
the 7-section outline from the structure sketch. Prose is moved verbatim; only
section headers, a few role-naming cross-reference sentences, and two new items
(a Notation table and a pipeline block diagram) are added. No content deleted."""
import re, io

src = open('paper/hp_sensitivity_v4.tex', encoding='utf-8').read().split('\n')

# --- split into preamble + ordered blocks keyed by first \label{sec:...} -----
# find the Introduction section start
start = next(i for i, l in enumerate(src) if l.startswith(r'\section{Introduction}'))
preamble = src[:start]

# block boundaries: every \section or \subsection line
bnds = [i for i in range(start, len(src))
        if src[i].startswith(r'\section{') or src[i].startswith(r'\subsection{')]
bnds.append(len(src))
blocks = []  # (header_line, key, lines)
for a, b in zip(bnds[:-1], bnds[1:]):
    chunk = src[a:b]
    # strip trailing separator comments / blank runs so we control spacing
    while chunk and (chunk[-1].strip() == '' or chunk[-1].startswith('% ===')):
        chunk.pop()
    m = re.search(r'\\label\{(sec:[^}]+)\}', '\n'.join(chunk[:3]))
    key = m.group(1) if m else ('nolabel:' + chunk[0][:40])
    blocks.append([chunk[0], key, chunk])

B = {k: lines for (_h, k, lines) in blocks}

def body_after_header(lines):
    return lines[2:] if re.match(r'\\label', lines[1]) else lines[1:]

def edit(lines, old, new):
    s = '\n'.join(lines).replace(old, new)
    return s.split('\n')

# ---- targeted prose/header edits (role-naming sentences & headers only) ------
# Introduction: rewrite the roadmap sentence for the new 7-section layout
B['sec:intro'] = edit(B['sec:intro'],
    r'The rest of the paper is structured as follows. Section~\ref{sec:problem} states the problem; Section~\ref{sec:fits} presents the two fits; Section~\ref{sec:usecases} describes the use cases derived from them; Section~\ref{sec:results} reports numerical results on Swiss data; Section~\ref{sec:validation} validates on a real unseen feeder; Section~\ref{sec:discussion} discusses accuracy, generalisability and data requirements; Section~\ref{sec:conclusion} concludes.',
    r'The rest of the paper is structured as follows. Section~\ref{sec:problem} states the problem and the approach; Section~\ref{sec:fits} presents the temperature-response functions, the capacity and energy quantities and their behaviour under aggregation; Section~\ref{sec:flex} quantifies flexibility; Section~\ref{sec:results} reports case studies on Swiss data and a real unseen feeder; Section~\ref{sec:discussion} discusses accuracy, generalisability and data requirements; Section~\ref{sec:conclusion} concludes.')

# Problem -> "Problem and Approach"; fix the closing pointer sentence
B['sec:problem'][0] = r'\section{Problem and Approach}'
B['sec:problem'] = edit(B['sec:problem'],
    r'Section~\ref{sec:fits} defines the functions which are fitted and used to quantify the aggregated ETL population, and Section~\ref{sec:usecases} derives the three quantities from them.',
    r'Section~\ref{sec:fits} defines the functions that are fitted and derives the installed-capacity and energy quantities from them, and Section~\ref{sec:flex} derives the flexibility.')

# Temperature-Response -> "Properties of Spatial and Temporal Aggregation"
B['sec:fits'][0] = r'\section{Properties of Spatial and Temporal Aggregation}'

# SF def: the "combines them" sentence pointed at the (now dissolved) use-case section
B['sec:fits-sf'] = edit(B['sec:fits-sf'],
    r'Section~\ref{sec:usecases} combines them,',
    r'Section~\ref{sec:uc-capacity} combines them,')

# Use-cases intro paragraph: drop the \section header + its label, keep the para as a bridge
uc = B['sec:usecases']
bridge = [l for l in body_after_header(uc)]   # paragraph only, no header/label

# Function Fits -> retitle as the aggregation-quality subsection of section 3
B['sec:res-ff'][0] = r'\subsection{Fit Quality across Aggregation}'

# Flexibility definition subsection -> promote to a top-level section (section 4)
fx = list(B['sec:uc-flex'])
fx[0] = r'\section{Flexibility Quantification Based on the Simultaneity Factor}'
# keep sec:uc-flex label and add sec:flex right after it
for i, l in enumerate(fx[:3]):
    if l.strip() == r'\label{sec:uc-flex}':
        fx.insert(i + 1, r'\label{sec:flex}')
        break
B['sec:uc-flex'] = fx

# Numerical Results -> "Case Studies"
B['sec:results'][0] = r'\section{Case Studies}'

# Dataset paragraph: "in this section" -> "in this study" (it now sits under Approach)
B['sec:data'] = edit(B['sec:data'],
    r'The data used in this section is a combination', r'The data used in this study is a combination')

# Validation: demote to a subsection of Case Studies, retitled as generalisation
B['sec:validation'][0] = r'\subsection{Generalisation to a Real Unseen Feeder}'

# ---- new content: notation table and pipeline block diagram ------------------
notation = r"""\subsection{Notation}
\label{sec:notation}
Table~\ref{tab:notation} lists the recurring symbols.
\begin{table}[t]
\caption{Notation}
\label{tab:notation}
\centering
\begin{tabular}{ll}
\toprule
Symbol & Meaning \\
\midrule
$P_{\mathrm{net}}(t)$ & aggregated net load \\
$P_{\mathrm{ETL}}(t)$ & aggregated ETL (heat-pump) load \\
$P_{\text{non-ETL}}(t)$ & aggregated non-ETL load \\
$P_{\mathrm{base}}$ & temperature-independent base load \\
$s_h,\ s_c$ & heating, cooling sensitivities [kW/$^\circ$C] \\
$T_h,\ T_c$ & heating, cooling threshold temperatures [$^\circ$C] \\
$P_{\mathrm{ETL}}^{\max}$ & ETL installed capacity \\
$\mathrm{SF}(T)$ & simultaneity factor \\
$b,\ m$ & SF base fraction, sensitivity [1/$^\circ$C] \\
$T_h^{\mathrm{SF}}$ & SF threshold temperature [$^\circ$C] \\
$T_{\min}$ & coldest recorded temperature [$^\circ$C] \\
$\alpha_F$ & flexibility duty cycle \\
$\Delta t_{Th}$ & thermal-inertia window [h] \\
$E_{\mathrm{flex}}$ & flexible energy [kWh] \\
$N,\ N_{hp}$ & consumers, HPs behind the meter \\
\bottomrule
\end{tabular}
\end{table}"""

pipeline = r"""\begin{figure}[t]
\centering
\begin{tikzpicture}[font=\scriptsize, >=latex,
  io/.style={draw, fill=black!6, rounded corners=1pt, align=center, minimum height=6mm, inner sep=2.5pt},
  proc/.style={draw, rounded corners=3pt, align=center, minimum height=6mm, inner sep=2.5pt},
  node distance=3.5mm and 7mm]
\node[io] (net) {Aggregated\\net load};
\node[io, below=of net] (temp) {Ambient\\temperature};
\node[io, above=of net] (sub) {Submetered\\ETL pilot};
\node[proc, right=of net] (bath) {Net-load fit\\Eq.~\eqref{eq:bathtub}};
\node[proc, right=of sub] (sf) {SF fit\\Eq.~\eqref{eq:sffit}};
\node[proc, right=9mm of bath] (cap) {Installed cap.\\Eq.~\eqref{eq:capacity}};
\node[proc, above=of cap] (en) {Energy\\Eq.~\eqref{eq:energy}};
\node[proc, right=of cap] (fl) {Flexibility\\Eq.~\eqref{eq:flex-energy}};
\draw[->] (net) -- (bath);
\draw[->] (temp) -| (bath);
\draw[->] (sub) -- (sf);
\draw[->] (bath) -- (cap);
\draw[->] (bath.north) |- (en.west);
\draw[->] (sf) -| (cap.north);
\draw[->] (cap) -- (fl);
\draw[->,dashed] (sf.east) -| (fl.north);
\end{tikzpicture}
\caption{Method pipeline. The observable net-load fit and a submetered-pilot SF fit combine into the installed capacity; the net-load fit alone gives the temperature-driven energy, and the capacity with the SF gives the flexibility. Dashed: the transferred SF also shapes the flexibility.}
\label{fig:pipeline}
\end{figure}"""

# ---- emit ---------------------------------------------------------------------
out = []
out += preamble
# inject TikZ packages after graphicx
for i, l in enumerate(out):
    if l.startswith(r'\usepackage{graphicx}'):
        out.insert(i + 1, r'\usepackage{tikz}')
        out.insert(i + 2, r'\usetikzlibrary{positioning,arrows.meta}')
        break

def sec(lines):
    out.append('')
    out.append('% ' + '=' * 69)
    out.extend(lines)

def sub(lines):
    out.append('')
    out.extend(lines)

sec(B['sec:intro'])
# Section 2: Problem and Approach
sec(B['sec:problem'])
sub(notation.split('\n'))
sub(pipeline.split('\n'))
sub(B['sec:data'])
# Section 3: Properties of Spatial and Temporal Aggregation
sec(B['sec:fits'])
sub(B['sec:fits-net'])
sub(B['sec:fits-sf'])
sub(bridge)
sub(B['sec:uc-capacity'])
sub(B['sec:uc-energy'])
sub(B['sec:res-ff'])
# Section 4: Flexibility
sec(B['sec:uc-flex'])
# Section 5: Case Studies
sec(B['sec:results'])
sub(B['sec:res-sf'])
sub(B['sec:res-capacity'])
sub(B['sec:res-energy'])
sub(B['sec:res-flex'])
sub(B['sec:validation'])
# Section 6: Discussion (+ its subsections in original order)
sec(B['sec:discussion'])
for _h, k, lines in blocks:
    if _h.startswith(r'\subsection') and k.startswith('nolabel:') and any(
        t in _h for t in ['Accuracy', 'Generalisation', 'Data Requirements', 'Limitations', 'Concluding']):
        sub(lines)
# Section 7: Conclusion
sec(B['sec:conclusion'])
out.append('')

open('paper/hp_sensitivity_v5.tex', 'w', encoding='utf-8').write('\n'.join(out))

# ---- integrity check: every non-empty source body line still present ---------
def prose(text):
    return [l.strip() for l in text if l.strip() and not l.strip().startswith('%')
            and not l.strip().startswith(r'\section') and not l.strip().startswith(r'\subsection')]
srcset = prose(src[start:])
outset = prose(out)
missing = [l for l in srcset if l not in outset]
print(f'v5 written: {len(out)} lines')
print(f'source body prose lines: {len(srcset)}, still present in v5: {len(srcset)-len(missing)}')
print(f'MISSING ({len(missing)}):')
for l in missing[:40]:
    print('   |', l[:100])
