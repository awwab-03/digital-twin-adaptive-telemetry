import io.github.xkitsios.*;
import io.github.xkitsios.util.*;
import java.io.*; import java.util.*;
/** Windowed Mix-Piece: compress the stream in consecutive windows of W points (one message per
 *  window). Writes length-prefixed pre-zstd payloads and the reconstructed values. */
public class WinRun {
  public static void main(String[] a) throws Exception {
    String data=a[0], out=a[1]; String[] names=a[2].split(","); double[] epsPct=Arrays.stream(a[3].split(",")).mapToDouble(Double::parseDouble).toArray();
    int[] Ws=Arrays.stream(a[4].split(",")).mapToInt(Integer::parseInt).toArray();
    for(String name: names){
      TimeSeries ts=TimeSeriesReader.getTimeSeries(new FileInputStream(data+"/"+name+".csv.gz"),",",true);
      List<Point> pts=ts.data; int n=pts.size();
      for(double ep: epsPct) for(int W: Ws){
        double eps=ts.range*ep/100.0;
        String base=String.format("%s/%s_e%.3f_W%d",out,name,ep,W);
        try(DataOutputStream pay=new DataOutputStream(new BufferedOutputStream(new FileOutputStream(base+".pay")));
            DataOutputStream rec=new DataOutputStream(new BufferedOutputStream(new FileOutputStream(base+".rec")))){
          long t0=System.nanoTime();
          for(int i=0;i<n;i+=W){
            List<Point> c=pts.subList(i,Math.min(i+W,n));
            byte[] b=MixPiece.compress(c,eps);
            pay.writeInt(b.length); pay.write(b);
            List<Point> d=MixPiece.decompress(b);
            int idx=0;
            for(Point p: d){ if(idx>=c.size()) break; if(p.getTimestamp()!=c.get(idx).getTimestamp()) continue; rec.writeDouble(p.getValue()); idx++; }
            if(idx!=c.size()) throw new RuntimeException("missing points");
          }
          System.out.printf("%s,%.3f,%d,%.1f%n",name,ep,W,(System.nanoTime()-t0)/1e6);
        }
      }
    }
  }
}
