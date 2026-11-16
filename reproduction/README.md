# Group 21 – Base-article reproduction (Mix-Piece / Sim-Piece)

Base article: Kitsios et al., "Flexible Grouping of Linear Segments for Highly Accurate Lossy Compression of Time Series Data", The VLDB Journal 33(5), 2024.
Official code: https://github.com/xkitsios/Sim-Piece (Apache-2.0)

## Reproduce
```bash
git clone https://github.com/xkitsios/Sim-Piece.git && git -C Sim-Piece checkout f4e875c   # commit used in our study
mkdir -p build data out/full out/window && cp Sim-Piece/src/test/resources/*.gz data/
SRC=Sim-Piece/src
javac -d build $(find shim $SRC/main $SRC/test/java/io/github/xkitsios/util -name "*.java") runner/Repro.java
java -Xmx5g -cp build Repro data out/full full                 # paper's epsilon grid, 12 datasets
java -Xmx5g -cp build Repro data out/window window \
  Cricket,FaceFour,Lightning,MoteStrain,Wafer,WindSpeed,WindDirection,BTCUSD,ETHUSD,SPX,STOXX50E   # batching-window (staleness) experiment
pip install zstandard numpy matplotlib reportlab
python3 analyze.py && python3 figs.py && python3 report.py
```
`shim/` replaces zstd-jni with a pass-through (Maven Central was unreachable); `analyze.py` applies real zstd (level 3, the zstd-jni default) to the exact byte streams.
Run the two Java jobs one after the other (running them together on 7 GB RAM ran out of memory).
