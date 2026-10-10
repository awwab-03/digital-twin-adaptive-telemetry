import json, numpy as np
from collections import defaultdict
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
R=json.load(open('results.json')); full=R['full']; win=R['window']; DB={d['dataset']:d for d in R['deadband']}
ss=getSampleStyleSheet()
B=ParagraphStyle('b',parent=ss['BodyText'],fontName='Times-Roman',fontSize=10.5,leading=14,spaceAfter=5,alignment=4)
H1=ParagraphStyle('h1',parent=ss['Heading1'],fontName='Times-Bold',fontSize=14,spaceBefore=10,spaceAfter=6)
H2=ParagraphStyle('h2',parent=ss['Heading2'],fontName='Times-Bold',fontSize=11.5,spaceBefore=8,spaceAfter=4)
T=ParagraphStyle('t',parent=ss['Title'],fontName='Times-Bold',fontSize=16,leading=20)
S=ParagraphStyle('s',parent=B,fontSize=8.5,leading=10.5,alignment=0)
CAP=ParagraphStyle('c',parent=B,fontSize=9,leading=11,alignment=1,textColor=colors.HexColor('#333333'))
def P(t,st=B): return Paragraph(t,st)
def bl(items): return [P('&bull;&nbsp; '+i) for i in items]
def tbl(data,cw=None,fs=8.5):
    data=[[Paragraph(str(c),S) for c in row] for row in data]
    t=Table(data,colWidths=cw,repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dfe7f2')),('GRID',(0,0),(-1,-1),0.4,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
    return t
st=[]
st+= [P('Base-Article Implementation and Research-Gap Report',T),
 P('<b>Cloud Computing 100-Day Research Assignment &mdash; Group 21</b><br/>Muhammad Awwab Aamir (22i-0971, Primary Researcher) &middot; Rayyan Khan (22i-1002, Co-Researcher)<br/>Research area: Digital Twins and Cloud Computing &middot; Project: Adaptive telemetry for cloud-hosted IoT digital twins<br/>Submitted: 10 October 2026',ParagraphStyle('x',parent=B,alignment=1)),Spacer(1,6)]
# 1
st+=[P('1. Selected Base Article',H1)]
st+=[tbl([['Field','Details'],
 ['Title','Flexible Grouping of Linear Segments for Highly Accurate Lossy Compression of Time Series Data (Mix-Piece)'],
 ['Authors','X. Kitsios, P. Liakos, K. Papakonstantinopoulou, Y. Kotidis'],
 ['Venue / Year','The VLDB Journal, Vol. 33, No. 5, pp. 1569&ndash;1589, 2024. DOI: 10.1007/s00778-024-00862-z'],
 ['Predecessor (in-paper baseline)','Sim-Piece, Proc. VLDB Endowment, Vol. 16, No. 8, pp. 1910&ndash;1922, 2023. DOI: 10.14778/3594512.3594521'],
 ['Paper link','https://xkitsios.github.io/assets/pdf/mixpiece-vldbj24.pdf'],
 ['Code (official)','https://github.com/xkitsios/Sim-Piece (Apache-2.0; contains both Mix-Piece and Sim-Piece)'],
 ['Our repository','https://github.com/awwab-03/digital-twin-adaptive-telemetry']],cw=[3.6*cm,13*cm])]
st+=[P('<b>Why this paper.</b> Our approved topic studies edge-side telemetry reduction (deadband / adaptive sampling) for cloud-hosted digital twins. Mix-Piece is a recent (2024), top-venue, state-of-the-art <i>error-bounded</i> lossy compressor for sensor time series, i.e. it solves the same problem our edge device faces: send fewer bytes to the cloud while guaranteeing that the twin\'s mirrored value never deviates from the physical value by more than a tolerance &epsilon;. It satisfies the reproducibility checklist of the assignment: an official public repository, released source, a benchmark script, bundled public datasets, and modest hardware needs (CPU only).')]
st+=[P('<b>Reproducibility verification (before selection).</b>',B)]
st+=[tbl([['Item','Available?','Notes'],
 ['Official GitHub repository','Yes','xkitsios/Sim-Piece'],
 ['Source code','Yes','MixPiece.java (404 LOC), SimPiece.java (244 LOC), encoders'],
 ['Experiment script','Yes','TestPLA.java (JUnit benchmark: compression ratio vs. &epsilon;)'],
 ['Datasets','Yes','12 datasets bundled as .csv.gz in src/test/resources'],
 ['Configuration','Partial','&epsilon; ranges hard-coded in TestPLA; no config file'],
 ['Software / libraries','Yes','Java 8+, Maven, zstd-jni 1.5.4-2, JUnit 5.9.1'],
 ['Hardware / cloud needs','Low','Single CPU machine; no GPU'],
 ['Install / run instructions','Minimal','One command: mvn test -Dtest=TestPLA'],
 ['Instructions to reproduce paper tables','No','Script reports compression ratio only; time/error figures of the paper need extra code']],cw=[5*cm,2.2*cm,9.4*cm])]
# 2
st+=[P('2. Understanding the Original Paper',H1)]
st+=[P('<b>Problem.</b> IoT and monitoring systems generate very long numeric time series. Storing and transmitting them raw is costly. Piecewise Linear Approximation (PLA) compresses a series into line segments such that every reconstructed point stays within a maximum absolute error &epsilon;. Existing PLA methods (e.g. optimal PLA, Swing/Slide filters, PMC-Mean) treat each segment independently, which limits compression.'),
 P('<b>Proposed solution.</b> Sim-Piece (2023) first builds disjoint angle-based segments, each with a <i>quantised</i> start value and a feasible range of slopes. Segments that share the same quantised start and have overlapping slope ranges are merged into groups that share one slope, so many segments are stored with a single value. The byte stream is then compressed with Zstandard. Mix-Piece (2024) extends this with flexible grouping (segments can join groups across different starting values) and better handling of trends, giving higher compression and lower error than Sim-Piece for the same &epsilon;.'),
 P('<b>Architecture.</b> Input series &rarr; (1) segment generation with quantised origins and slope intervals &rarr; (2) grouping / merging (greedy minimum-group search) &rarr; (3) variable-byte encoding of groups and timestamps &rarr; (4) Zstandard &rarr; compact binary. Decompression reverses the steps.'),
 P('<b>Cloud computing component.</b> The paper is a data-management contribution; its cloud relevance is reducing the volume of sensor data that must be shipped to and stored in cloud back-ends (ingestion bandwidth, egress and storage cost). The paper does <i>not</i> evaluate an edge-to-cloud pipeline, ingestion latency or a digital twin consumer &mdash; this becomes our research gap (Section 6).'),
 P('<b>Multimodal component.</b> Not applicable: the method handles univariate numeric time series (one sensor channel at a time). Multimodal data was listed as preferred, not mandatory; our project is single-modality telemetry by design.'),
 P('<b>Baselines (as listed by the authors).</b> Optimal PLA (the authors\' summary figure normalises against it), Sim-Piece, and other PLA techniques. <b>Metrics:</b> compression ratio (raw size / compressed size, raw = 8 bytes per point: 4-byte timestamp + 4-byte float), MAE and RMSE at equal space, and compression time. <b>Hyper-parameter:</b> the error bound &epsilon;, expressed as a percentage of the signal range (max &minus; min): 0.5&ndash;5% for sensor datasets and 0.05&ndash;0.5% for high-precision ones.'),
 P('<b>Assumptions.</b> (i) The whole series (or a large block) is available before compression &mdash; grouping is global; (ii) a fixed, user-chosen &epsilon; for the whole series; (iii) only the L&infin; error bound is guaranteed; (iv) single channel, regular timestamps. <b>Unclear / missing details:</b> the released script does not reproduce the timing and MAE/RMSE figures; the decompressor guesses the output buffer size (code comment: <i>&ldquo;How to know apriori original size?&rdquo;</i>); no streaming API is offered (README &ldquo;Using the Library: TODO&rdquo;).')]
# 3 datasets
st+=[P('3. Datasets',H1)]
dsinfo={'Cricket':('UCR archive','Accelerometer (human motion)'),'FaceFour':('UCR archive','Shape outline series'),'Lightning':('UCR archive','Electromagnetic sensor (FORTE satellite)'),'MoteStrain':('UCR archive','Wireless sensor-mote readings'),'Wafer':('UCR archive','Semiconductor process sensor'),'WindSpeed':('Environmental sensor','Wind speed'),'WindDirection':('Environmental sensor','Wind direction (degrees)'),'Pressure':('Environmental sensor','Atmospheric pressure'),'BTCUSD':('Finance','Bitcoin price'),'ETHUSD':('Finance','Ethereum price'),'SPX':('Finance','S&amp;P 500 index'),'STOXX50E':('Finance','EURO STOXX 50 index')}
nmap={}
for r in full: nmap[r['dataset']]=int(r['n'])
rows=[['Dataset','Points (counted)','Type / modality','Characteristics','&epsilon; range used']]
for d in ['Cricket','FaceFour','Lightning','MoteStrain','Wafer','WindSpeed','WindDirection','Pressure','BTCUSD','ETHUSD','SPX','STOXX50E']:
    rows.append([d,f'{nmap[d]:,}',dsinfo[d][0],dsinfo[d][1],'0.05&ndash;0.5%' if d in ['Pressure','BTCUSD','ETHUSD','SPX','STOXX50E'] else '0.5&ndash;5%'])
st+=[tbl(rows,cw=[2.6*cm,2.6*cm,3.2*cm,5.2*cm,2.6*cm])]
st+=[P('All 12 series are bundled in the official repository as two-column gzip CSVs (timestamp index, value); point counts above were counted by us. All are univariate numeric (single modality). <b>Splits:</b> none &mdash; compression is unsupervised, every point is compressed. <b>Preprocessing:</b> none beyond parsing; values are read as doubles and the signal range is computed to scale &epsilon;. <b>Filtering/augmentation:</b> none. The UCR-derived series are concatenations of archive instances; exact provenance of the environmental and finance series is given in the paper\'s dataset section (to be cited precisely in the manuscript).')]
# 4 environment
st+=[P('4. Reproduction Setup',H1)]
st+=[tbl([['Item','Value'],['Hardware','Cloud VM, 2 vCPU Intel Xeon @ 2.10 GHz, 7 GB RAM, no GPU'],['OS','Ubuntu 24.04.5 LTS'],['Java / build','OpenJDK 21.0.12, Apache Maven 3.9.11 (javac used directly, see deviations)'],['Python (analysis)','Python 3.13, numpy 2.5, zstandard 0.25 (libzstd), matplotlib 3.11'],['Code version','xkitsios/Sim-Piece, main branch, cloned 10 Oct 2026'],['Configuration','Exactly the &epsilon; grids of TestPLA.java: 0.5%:0.5%:5% (7 datasets), 0.05%:0.05%:0.5% (5 datasets); raw size = 8 bytes/point'],['Correctness check','Every decompressed point verified against &epsilon; (same 1.1&epsilon; tolerance as the authors\' test)']],cw=[3.6*cm,13*cm])]
st+=[P('<b>Deviation from the original pipeline.</b> Our cloud VM blocks Maven Central, so <i>mvn test</i> failed (could not resolve junit-bom and zstd-jni). We compiled the authors\' sources directly with javac, replaced the JUnit harness with an equivalent main() runner (same datasets, same &epsilon; grid, same verification), and replaced the zstd-jni call with a pass-through shim; the exact intermediate byte stream was written to disk and compressed with libzstd at level 3 (the zstd-jni default) in Python. Because Zstandard is deterministic for a given level and input, the final sizes match what Zstd.compress() produces up to library-version differences (zstd-jni 1.5.4 vs. our libzstd build).')]
# 5 results
st+=[P('5. Reproduced Results',H1)]
agg=defaultdict(dict)
for r in full: agg[(r['dataset'],r['method'])][float(r['eps_pct'])]=r
rows=[['Dataset','Mix-Piece CR (lowest &epsilon;)','Mix-Piece CR (highest &epsilon;)','Sim-Piece CR (lowest &epsilon;)','Sim-Piece CR (highest &epsilon;)','Mean Mix/Sim ratio','Bound held']]
ratios=[]; allok=True
for d in ['Cricket','FaceFour','Lightning','MoteStrain','Wafer','WindSpeed','WindDirection','Pressure','BTCUSD','ETHUSD','SPX','STOXX50E']:
    m=agg[(d,'MixPiece')]; s=agg[(d,'SimPiece')]; e=sorted(m)
    rr=[m[x]['cr']/s[x]['cr'] for x in e]; ratios+=rr
    ok=all(m[x]['bound_ok'] for x in e) and all(s[x]['bound_ok'] for x in e); allok&=ok
    rows.append([d,f"{m[e[0]]['cr']:.2f}",f"{m[e[-1]]['cr']:.2f}",f"{s[e[0]]['cr']:.2f}",f"{s[e[-1]]['cr']:.2f}",f"{np.mean(rr):.3f}",'Yes' if ok else 'No'])
st+=[tbl(rows,cw=[2.4*cm,2.4*cm,2.4*cm,2.4*cm,2.4*cm,2.3*cm,1.6*cm])]
st+=[P('Table 3. Reproduced compression ratios (CR) for all 12 datasets, at the smallest and largest &epsilon; of each grid (full 240-run grid is in results.json in our repository).',CAP)]
gm=float(np.exp(np.mean(np.log(ratios)))); am=float(np.mean(ratios))
wins=sum(1 for x in ratios if x>1)
st+=[Image('fig1.png',width=17*cm,height=4.4*cm),P('Figure 1. Reproduced CR vs. &epsilon; for four representative datasets.',CAP)]
st+=[P('<b>Original vs. reproduced.</b> The repository publishes the authors\' summary result: average CR relative to optimal PLA of 1.8 for Sim-Piece and 2.1 for Mix-Piece. We did not implement optimal PLA tonight, so we compare the quantity that can be derived from both: the Mix-Piece / Sim-Piece CR ratio.')]
st+=[tbl([['Result','Original paper','Reproduced','Difference'],
 ['Mix-Piece / Sim-Piece CR ratio (mean over datasets and &epsilon;)','2.1 / 1.8 = 1.167',f'{am:.3f} (arithmetic), {gm:.3f} (geometric)',f'{(am-1.1667)/1.1667*100:+.1f}%'],
 ['Fraction of (dataset, &epsilon;) cases where Mix-Piece &gt; Sim-Piece','Mix-Piece reported better overall',f'{wins}/{len(ratios)}','&mdash;'],
 ['Error bound guaranteed for every point','Yes (by design)','Yes' if allok else 'No (see text)','None'],
 ['Per-dataset CR / time / RMSE tables','In paper','CR reproduced for 12 datasets (Table 3)','Paper tables to be transcribed for per-cell comparison']],cw=[5.5*cm,3.6*cm,4.2*cm,3.3*cm])]
st+=[P('<b>Interpretation and possible reasons for differences.</b> The direction of the result is reproduced: Mix-Piece compresses more than Sim-Piece and both always respect the error bound. Exact agreement with the 2.1/1.8 figure is not expected because (i) the authors\' figure averages CR <i>relative to optimal PLA</i> per dataset, while our ratio is taken directly between the two methods (different averaging); (ii) the public repository is packaged as a library release (v1.0.0-RC1) that may differ from the exact code used for the paper\'s experiments; (iii) zstd library version differs (zstd-jni 1.5.4 vs. our libzstd); (iv) the averaging over datasets and &epsilon; used by the authors is not specified in the repository. Runtime is not comparable (different CPU, JDK 21 vs. the authors\' JVM).')]
st+=[P('<b>Problems encountered.</b> (1) Installation: Maven could not resolve dependencies or the Sonatype publishing plugin from our network &mdash; worked around with direct javac compilation and a zstd shim. (2) Missing resources: no script for the time and MAE/RMSE experiments, no optimal-PLA implementation in the repository. (3) Code issues: decompression assumes the output is at most 2&times; the input size (a TODO in the code); README usage section is empty. (4) Computational limits: the 12.1-million-point Pressure series dominates run time on 2 vCPUs but completes. (5) Paper PDF tables could not be fetched automatically in our environment and will be transcribed manually for the final comparison.')]
# 6 gap
st+=[P('6. Identified Research Gap',H1)]
wrows=[['Dataset','W=32','W=128','W=512','W=2048','Whole series','Online deadband (W=1)']]
byd=defaultdict(dict)
for r in win:
    if r['method']=='MixPiece': byd[r['dataset']][int(r['window'])]=r['cr']
low=[]
for d in ['Cricket','FaceFour','Lightning','MoteStrain','Wafer','WindSpeed','WindDirection','Pressure','BTCUSD','ETHUSD','SPX','STOXX50E']:
    if d not in byd: continue
    b=byd[d]; dbv=DB.get(d,{}).get('cr',float('nan'))
    wrows.append([d]+[f"{b.get(w,float('nan')):.2f}" for w in [32,128,512,2048,0]]+[f'{dbv:.2f}'])
    if 32 in b and 0 in b: low.append(b[32]/b[0])
st+=[P('Our critical analysis of the reproduced system points to one central limitation that matters for digital twins in the cloud: <b>Mix-Piece/Sim-Piece are batch, offline compressors.</b> Grouping is global, so the encoder must buffer many points before it can transmit anything. A cloud-hosted digital twin, however, needs a <i>fresh</i> mirror of the physical asset: every point held in the edge buffer is staleness the twin cannot see. We tested this directly with the authors\' code by forcing it to compress in windows of W points (i.e. a twin staleness of up to W sampling periods), at a mid-range &epsilon; (2.5% of range; 0.25% for high-precision datasets), and compared it with the simplest online scheme, a send-on-delta deadband filter that transmits a point the instant it deviates more than &epsilon; from the last sent value (8 bytes per message, no buffering, same L&infin; guarantee).')]
st+=[tbl(wrows,cw=[2.6*cm,1.9*cm,1.9*cm,1.9*cm,1.9*cm,2.4*cm,3.6*cm])]
st+=[P('Table 5. Preliminary gap evidence: Mix-Piece CR as a function of the batching window W (twin staleness) vs. an unbuffered deadband baseline at the same &epsilon;. Each window is zstd-compressed independently (one message per flush). Pressure (12.1 M points) omitted from this experiment for time reasons; it will be added for Cutoff 3.',CAP)]
st+=[Image('fig2.png',width=17*cm,height=6.5*cm),P('Figure 2. Mix-Piece CR collapses as the latency budget (window W) shrinks; red dashed line = online deadband with zero buffering.',CAP)]
st+=[P('<b>Finding.</b>' + f' At W=32 Mix-Piece keeps on average only {np.mean(low)*100:.0f}% of its whole-series compression ratio (range {min(low)*100:.0f}&ndash;{max(low)*100:.0f}% across datasets). Its headline advantage therefore depends on large buffers, i.e. on twin staleness that is unacceptable for real-time monitoring. Strikingly, the unbuffered deadband (zero added staleness, no entropy coding) already achieves a higher CR than Mix-Piece at W=32 on '+str(sum(1 for d in byd if d in DB and DB[d]['cr']>byd[d][32]))+' of '+str(sum(1 for d in byd if d in DB))+' datasets, while Mix-Piece wins clearly once W is in the hundreds or thousands. The best scheme thus depends on the twin\'s freshness budget, which motivates a latency-aware design. The base paper does not measure this <b>compression&ndash;staleness&ndash;fidelity trade-off on an actual edge-to-cloud ingestion path</b>, and the PLA baselines it compares with are likewise evaluated offline; this will be confirmed against the broader literature in the manuscript.')]
st+=[P('<b>Gap statement.</b> State-of-the-art error-bounded time-series compressors are evaluated offline on compression ratio and error only; their behaviour under the latency (freshness) constraints of cloud-hosted digital twins, and the resulting cloud ingestion cost (message count, bytes, p50/p95 ingestion latency) and twin state fidelity, are unmeasured. Moreover, both the base method and deadband use a single fixed &epsilon; for the whole signal, even though sensor volatility changes over time.')]
st+=[P('This gap is grounded in our reproduction rather than in the novelty of a technique: it falls under the assignment\'s categories <i>high latency</i>, <i>limited evaluation scenarios</i> and <i>lack of real-world (cloud) evaluation</i>.')]
# 7 proposed
st+=[P('7. Proposed Methodology',H1)]
st+=[P('<b>Refined RQ.</b> Under a fixed twin-freshness budget (maximum staleness T<sub>max</sub>) and fidelity budget (&epsilon;), can a latency-aware adaptive telemetry scheme at the edge reduce cloud ingestion bytes, message count and p95 ingestion latency relative to fixed-rate streaming and to windowed Mix-Piece, while keeping digital-twin RMSE within budget?')]
st+=bl(['<b>Component A &mdash; Adaptive deadband.</b> An online send-on-delta filter whose threshold &epsilon;(t) adapts to recent signal volatility (rolling standard deviation), bounded by the twin\'s fidelity budget, plus a heartbeat so the twin never goes silent longer than T<sub>max</sub>.',
 '<b>Component B &mdash; Deadline-bounded micro-batching.</b> Points that pass the deadband filter are buffered and flushed as one message either when the buffer would violate T<sub>max</sub> or when it reaches the cloud broker\'s message size quantum, with optional Mix-Piece encoding of each flush. This targets per-message cloud cost without exceeding the freshness budget.',
 '<b>Cloud pipeline.</b> Simulated edge clients replay the 12 public datasets (plus our synthetic temperature/vibration generator) at fixed rates (e.g. 50 Hz) to an MQTT broker &rarr; ingestion service &rarr; time-series database acting as the digital twin. Deployed with Docker on a cloud VM (provider-agnostic).',
 '<b>Baselines.</b> (1) Fixed-rate continuous streaming; (2) reproduced Mix-Piece with window W; (3) fixed-&epsilon; deadband.',
 '<b>Metrics.</b> Bytes and messages per hour at the broker; p50/p95 end-to-end ingestion latency (edge timestamp &rarr; DB write); twin staleness; RMSE and max error between the physical signal and the twin state; edge CPU time.',
 '<b>Ablation (assignment step 11).</b> Baseline; +A only; +B only; +A+B &mdash; each at three &epsilon; and three T<sub>max</sub> levels, 5 repeated runs with mean and 95% CI.'])
st+=[P('8. Status and Next Steps',H1)]
st+=[tbl([['Assignment step','Status'],['1&ndash;4 Select, verify, document datasets, understand paper','Done (this report)'],['5&ndash;6 Reproduce main results, reproduction report','Done for compression ratio on all 12 datasets; per-cell comparison with paper tables pending transcription'],['7 Identify research gap','Done, supported by our own windowed experiment (Table 5)'],['8 Discuss gap with mentor','Requested &mdash; this report is the basis'],['9 Design and implement improvement','Design done (Section 7); implementation started (deadband baseline already run)'],['10&ndash;12 Evaluation, ablation, final comparison','Planned for Cutoff 3 (2 November 2026)']],cw=[7*cm,9.6*cm])]
st+=[P('<b>Integrity note.</b> All numbers in this report were produced by running the authors\' released code and our scripts on the bundled public data on 10 October 2026; nothing was estimated. Code, raw results and figure scripts are publicly available at https://github.com/awwab-03/digital-twin-adaptive-telemetry (folder reproduction/).')]
st+=[P('References',H1)]
st+=[P('[1] X. Kitsios, P. Liakos, K. Papakonstantinopoulou, Y. Kotidis, &ldquo;Flexible grouping of linear segments for highly accurate lossy compression of time series data,&rdquo; <i>The VLDB Journal</i>, vol. 33, no. 5, pp. 1569&ndash;1589, 2024, doi:10.1007/s00778-024-00862-z.'),
 P('[2] X. Kitsios, P. Liakos, K. Papakonstantinopoulou, Y. Kotidis, &ldquo;Sim-Piece: Highly accurate piecewise linear approximation through similar segment merging,&rdquo; <i>Proc. VLDB Endowment</i>, vol. 16, no. 8, pp. 1910&ndash;1922, 2023, doi:10.14778/3594512.3594521.'),
 P('[3] Official code: https://github.com/xkitsios/Sim-Piece (Apache License 2.0).')]
doc=SimpleDocTemplate('G21_BaseArticle_Reproduction_and_Gap_Report.pdf',pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,topMargin=1.8*cm,bottomMargin=1.8*cm,title='Group 21 Base-Article Reproduction and Research Gap',author='M. Awwab Aamir, Rayyan Khan')
doc.build(st); print('pdf ok')
