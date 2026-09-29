// #! csharp
using System;
using System.Linq;
using System.Text;
using System.Globalization;
using System.Collections.Generic;
using Rhino;
using Rhino.Geometry;
using Rhino.DocObjects;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Types;

public class Script_Instance : GH_ScriptInstance
{
  StringBuilder sb; bool firstItem; CultureInfo ci = CultureInfo.InvariantCulture;
  Dictionary<string,int> stats;

  string F(double d){ return Math.Round(d, 3).ToString(ci); }
  string Hex(System.Drawing.Color c){ return "#" + c.R.ToString("X2") + c.G.ToString("X2") + c.B.ToString("X2"); }
  string Esc(string s){ return (s ?? "").Replace("\\","\\\\").Replace("\"","\\\"").Replace("\r","").Replace("\n","\\n").Replace("\t"," "); }

  class St { public string col; public double w; public string lt; public string dash; public int layer; public string lname; }

  void Emit(string type, St st, IEnumerable<IEnumerable<Point3d>> rings, bool fill, bool closed, string extra)
  {
    var rl = rings.Select(r => r.ToList()).Where(r => r.Count > 0).ToList();
    if (rl.Count == 0) return;
    if (!firstItem) sb.Append(",\n"); firstItem = false;
    sb.Append("{\"t\":\"").Append(type).Append("\",\"c\":\"").Append(st.col).Append("\",\"w\":").Append(F(st.w))
      .Append(",\"lt\":\"").Append(Esc(st.lt)).Append("\",\"d\":[").Append(st.dash).Append("],\"L\":\"").Append(Esc(st.lname))
      .Append("\",\"f\":").Append(fill ? 1 : 0).Append(",\"z\":").Append(closed ? 1 : 0);
    if (extra != null) sb.Append(",").Append(extra);
    sb.Append(",\"p\":[");
    for (int i = 0; i < rl.Count; i++) {
      if (i > 0) sb.Append(",");
      sb.Append("[");
      for (int j = 0; j < rl[i].Count; j++) { if (j > 0) sb.Append(","); sb.Append(F(rl[i][j].X)).Append(",").Append(F(rl[i][j].Y)); }
      sb.Append("]");
    }
    sb.Append("]}");
    stats[type] = stats.ContainsKey(type) ? stats[type] + 1 : 1;
  }

  List<Point3d> Pl(Curve c)
  {
    if (c == null) return new List<Point3d>();
    Polyline pl;
    if (c.TryGetPolyline(out pl)) return pl.ToList();
    var pc = c.ToPolyline(0.01, 0.03, 0, 0);
    if (pc != null && pc.TryGetPolyline(out pl)) return pl.ToList();
    var ts = c.DivideByCount(64, true); if (ts == null) return new List<Point3d>();
    var r = ts.Select(t => c.PointAt(t)).ToList(); if (c.IsClosed) r.Add(r[0]); return r;
  }

  void Geo(GeometryBase g, St st, int depth)
  {
    if (g == null || depth > 4) return;
    if (g is TextEntity) {
      var te = (TextEntity)g;
      Curve[] cs = null;
      try { cs = te.Explode(); } catch {}
      var ex = "\"s\":\"" + Esc(te.PlainText) + "\",\"h\":" + F(te.TextHeight) + ",\"o\":[" + F(te.Plane.Origin.X) + "," + F(te.Plane.Origin.Y) + "],\"a\":" + F(Math.Atan2(te.Plane.XAxis.Y, te.Plane.XAxis.X));
      if (cs != null && cs.Length > 0) Emit("text", st, cs.Select(Pl).Cast<IEnumerable<Point3d>>(), true, true, ex);
      else Emit("text0", st, new[]{ new[]{ te.Plane.Origin } }, false, false, ex);
      return;
    }
    if (g is Dimension) {
      GeometryBase[] parts = null;
      try { parts = ((Dimension)g).Explode(); } catch {}
      if (parts != null) foreach (var p in parts) Geo(p, st, depth + 1);
      else stats["dimfail"] = stats.ContainsKey("dimfail") ? stats["dimfail"] + 1 : 1;
      return;
    }
    if (g is Hatch) {
      var h = (Hatch)g;
      var doc = RhinoDoc.ActiveDoc;
      HatchPattern hp = (doc != null && h.PatternIndex >= 0 && h.PatternIndex < doc.HatchPatterns.Count) ? doc.HatchPatterns[h.PatternIndex] : null;
      bool solid = hp == null || hp.FillType == HatchPatternFillType.Solid;
      var rings = new List<IEnumerable<Point3d>>();
      foreach (var c in h.Get3dCurves(true)) rings.Add(Pl(c));
      foreach (var c in h.Get3dCurves(false)) rings.Add(Pl(c));
      var ex = "\"hp\":\"" + Esc(hp != null ? hp.Name : "?") + "\"";
      if (solid) Emit("hatch", st, rings, true, true, ex);
      else {
        Emit("hatchb", st, rings, false, true, ex);
        GeometryBase[] parts = null; try { parts = h.Explode(); } catch {}
        if (parts != null) foreach (var p in parts) if (p is Curve) Emit("hatchl", st, new[]{ Pl((Curve)p) }, false, false, ex);
      }
      return;
    }
    if (g is Point) { Emit("pt", st, new[]{ new[]{ ((Point)g).Location } }, false, false, null); return; }
    if (g is Curve) { var c = (Curve)g; Emit("crv", st, new[]{ Pl(c) }, false, c.IsClosed, null); return; }
    if (g is Brep || g is Surface || g is Extrusion) {
      Brep b = g is Brep ? (Brep)g : (g is Surface ? ((Surface)g).ToBrep() : ((Extrusion)g).ToBrep());
      foreach (var f in b.Faces) {
        var rings = new List<IEnumerable<Point3d>>();
        foreach (var lp in f.Loops) rings.Add(Pl(lp.To3dCurve()));
        Emit("face", st, rings, true, true, null);
      }
      return;
    }
    stats["other:" + g.GetType().Name] = 1;
  }

  St Style(object a)
  {
    var st = new St{ col = "#000000", w = 0, lt = "Continuous", dash = "", layer = -1, lname = "" };
    if (a == null) return st;
    var doc = RhinoDoc.ActiveDoc;
    var oa = a.GetType().GetProperty("Attributes")?.GetValue(a) as ObjectAttributes;
    var ly = a.GetType().GetProperty("Layer")?.GetValue(a) as Layer;
    if (ly == null && oa != null && doc != null && oa.LayerIndex >= 0 && oa.LayerIndex < doc.Layers.Count) ly = doc.Layers[oa.LayerIndex];
    if (ly != null) st.lname = ly.FullPath ?? ly.Name;
    System.Drawing.Color col = ly != null ? ly.Color : System.Drawing.Color.Black;
    double w = ly != null ? ly.PlotWeight : 0;
    int lti = ly != null ? ly.LinetypeIndex : -1;
    if (oa != null) {
      if (oa.ColorSource == ObjectColorSource.ColorFromObject) col = oa.ObjectColor;
      if (oa.PlotWeightSource == ObjectPlotWeightSource.PlotWeightFromObject) w = oa.PlotWeight;
      if (oa.LinetypeSource == ObjectLinetypeSource.LinetypeFromObject) lti = oa.LinetypeIndex;
    }
    st.col = Hex(col); st.w = w;
    if (doc != null && lti >= 0 && lti < doc.Linetypes.Count) {
      var lt = doc.Linetypes[lti]; st.lt = lt.Name;
      var ds = new List<string>();
      for (int i = 0; i < lt.SegmentCount; i++) { double len; bool solid; lt.GetSegment(i, out len, out solid); ds.Add(F(len)); }
      if (lt.SegmentCount > 1) st.dash = string.Join(",", ds);
    }
    return st;
  }

  private void RunScript(DataTree<object> G, DataTree<object> A, string v, ref object info)
  {
    var g = Component.Params.Input[0].VolatileData;
    var a = Component.Params.Input[1].VolatileData;
    sb = new StringBuilder(); firstItem = true; stats = new Dictionary<string,int>();
    sb.Append("{\"v\":\"").Append(Esc(v)).Append("\",\"items\":[\n");
    int n = Math.Min(g.PathCount, a.PathCount);
    for (int i = 0; i < n; i++) {
      var gb = g.get_Branch(g.Paths[i]); var ab = a.get_Branch(a.Paths[i]);
      for (int j = 0; j < gb.Count; j++) {
        var goo = gb[j] as IGH_Goo; if (goo == null) continue;
        object at = j < ab.Count ? ab[j] : null;
        var st = Style(at);
        object sv = goo.ScriptVariable();
        GeometryBase geo = null;
        if (sv is GeometryBase) geo = (GeometryBase)sv;
        else if (sv is Point3d) geo = new Point((Point3d)sv);
        else if (sv is Line) geo = new LineCurve((Line)sv);
        else if (sv is Circle) geo = new ArcCurve((Circle)sv);
        else if (sv is Arc) geo = new ArcCurve((Arc)sv);
        else if (sv is Rectangle3d) geo = ((Rectangle3d)sv).ToNurbsCurve();
        else if (sv is Polyline) geo = new PolylineCurve((Polyline)sv);
        else if (sv is Box) geo = ((Box)sv).ToBrep();
        if (geo == null) { stats["skip:" + (sv == null ? "null" : sv.GetType().Name)] = 1; continue; }
        Geo(geo, st, 0);
      }
    }
    sb.Append("\n]}");
    var dir = @"C:\Users\adel\Desktop\cordyceps\frames";
    System.IO.Directory.CreateDirectory(dir);
    System.IO.File.WriteAllText(System.IO.Path.Combine(dir, (v ?? "x").Trim() + ".json"), sb.ToString());
    info = stats.Select(kv => kv.Key + ": " + kv.Value).ToList();
  }
}
