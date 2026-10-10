import io.github.xkitsios.*;
import io.github.xkitsios.util.*;
import java.io.*; import java.util.*;
public class Repro {
  static double maxErr(List<Point> ts, List<Point> dec){
    int idx=0; double m=0;
    for(Point e: dec){ if(idx>=ts.size()) break; Point a=ts.get(idx); if(e.getTimestamp()!=a.getTimestamp()) continue; idx++; m=Math.max(m,Math.abs(a.getValue()-e.getValue())); }
    if(idx!=ts.size()) throw new RuntimeException("missing points "+idx+"/"+ts.size());
    return m;
  }
  static double[] errs(List<Point> ts, List<Point> dec){ // rmse, mae
    int idx=0; double s=0,a2=0;
    for(Point e: dec){ if(idx>=ts.size()) break; Point a=ts.get(idx); if(e.getTimestamp()!=a.getTimestamp()) continue; idx++; double d=a.getValue()-e.getValue(); s+=d*d; a2+=Math.abs(d);}
    return new double[]{Math.sqrt(s/ts.size()), a2/ts.size()};
  }
  public static void main(String[] args) throws Exception {
    String dir=args[0], outdir=args[1]; String mode=args[2]; // full | window
    String[] f1={"Cricket","FaceFour","Lightning","MoteStrain","Wafer","WindSpeed","WindDirection"};
    String[] f2={"Pressure","BTCUSD","ETHUSD","SPX","STOXX50E"};
    PrintWriter meta=new PrintWriter(new FileWriter(outdir+"/meta_"+mode+".csv"));
    meta.println("dataset,method,eps_pct,window,n,raw_bytes,payload_file,max_err,eps_abs,rmse,mae,ms");
    List<String> all=new ArrayList<>(); all.addAll(Arrays.asList(f1)); all.addAll(Arrays.asList(f2));
    if(args.length>3) all=Arrays.asList(args[3].split(","));
    for(String name: all){
      TimeSeries ts=TimeSeriesReader.getTimeSeries(new FileInputStream(dir+"/"+name+".csv.gz"),",",true);
      boolean fin=Arrays.asList(f2).contains(name);
      double[] epsList = new double[10]; for(int i=0;i<10;i++) epsList[i]= fin? 0.0005*(i+1) : 0.005*(i+1);
      int[] windows = mode.equals("full")? new int[]{0} : new int[]{32,128,512,2048,0};
      if(mode.equals("window")) epsList = new double[]{ fin?0.0025:0.025 };
      for(int w: windows) for(String m: new String[]{"MixPiece","SimPiece"}) for(double ep: epsList){
        double eps=ts.range*ep; long t0=System.nanoTime();
        List<List<Point>> chunks=new ArrayList<>();
        if(w==0) chunks.add(ts.data); else for(int i=0;i<ts.data.size();i+=w) chunks.add(ts.data.subList(i,Math.min(i+w,ts.data.size())));
        String pf=String.format("%s/%s_%s_%s_%d", "payloads", name, m, String.format("%.4f",ep), w);
        new File(outdir+"/"+pf).mkdirs();
        double mx=0; double se=0, ae=0; int ci=0;
        for(List<Point> c: chunks){
          byte[] b = m.equals("MixPiece")? MixPiece.compress(c,eps) : SimPiece.compress(c,eps);
          List<Point> d = m.equals("MixPiece")? MixPiece.decompress(b) : SimPiece.decompress(b);
          mx=Math.max(mx,maxErr(c,d)); double[] e=errs(c,d); se+=e[0]*e[0]*c.size(); ae+=e[1]*c.size();
          try(FileOutputStream fo=new FileOutputStream(outdir+"/"+pf+"/"+(ci++)+".bin")){fo.write(b);}
        }
        double ms=(System.nanoTime()-t0)/1e6;
        int n=ts.data.size();
        meta.printf("%s,%s,%.4f,%d,%d,%d,%s,%.6g,%.6g,%.6g,%.6g,%.1f%n",name,m,ep*100,w,n,ts.size,pf,mx,eps,Math.sqrt(se/n),ae/n,ms);
        meta.flush();
      }
      System.out.println("done "+name);
    }
    meta.close();
  }
}
