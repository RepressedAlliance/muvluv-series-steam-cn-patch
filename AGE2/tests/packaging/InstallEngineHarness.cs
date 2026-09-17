using System;
using System.IO;
using System.Linq;
using System.Text;
public static class InstallEngineHarness {
    static void Assert(bool ok, string message) { if (!ok) throw new Exception(message); }
    public static int Main(string[] args) {
        try {
            if(args.Length==1) { Age2InstallEngine.Verify(args[0]); Console.WriteLine("PASS: package verified"); return 0; }
            string package=args[0], game=args[1], profile=args[2];
            var m=Age2InstallEngine.Verify(package);
            string exe=Path.Combine(game,m.exe), root=Path.Combine(profile,"ancr",m.game,"data","root");
            string user=Path.Combine(profile,"ancr",m.game,"data","user","savedata.bin");
            string before=Age2InstallEngine.Hash(File.ReadAllBytes(exe));
            string receipt=Age2InstallEngine.Install(package,game,profile,Console.WriteLine);
            Assert(Age2InstallEngine.Hash(File.ReadAllBytes(exe))==m.native.patched_sha256,"Patched executable mismatch");
            Assert(File.ReadAllText(user)=="PLAYER-SAVE","Player save changed");
            Assert(!File.Exists(Path.Combine(root,"legacy-jp.txt")),"Old overlay remains active");
            Assert(Directory.GetFiles(Path.Combine(profile,"ancr",m.game,"data",".age2-cn-backups"),"legacy-jp.txt",SearchOption.AllDirectories).Length==1,"Old overlay not preserved");
            Assert(Age2InstallEngine.Hash(File.ReadAllBytes(Path.Combine(game,".age2-cn","original.exe")))==before,"Original executable not retained");
            Age2InstallEngine.Install(package,game,profile,null);
            Assert(File.ReadAllText(user)=="PLAYER-SAVE","Reinstall changed save");
            string payload=Path.Combine(package,"game","age2-cn.js");byte[] good=File.ReadAllBytes(payload);
            File.AppendAllText(payload,"corrupt");
            bool rejected=false;try {Age2InstallEngine.Install(package,game,profile,null);}catch(IOException){rejected=true;}
            File.WriteAllBytes(payload,good);
            Assert(rejected,"Corrupt payload accepted");
            byte[] patched=File.ReadAllBytes(exe);File.WriteAllText(exe,"wrong-version");
            rejected=false;try {Age2InstallEngine.Install(package,game,profile,null);}catch(IOException){rejected=true;}
            File.WriteAllBytes(exe,patched);Assert(rejected,"Wrong game version accepted");
            // Hold a runtime component open at commit time so earlier mutations
            // must be undone, including the root directory switch.
            FileStream locked=null;bool rolledBack=false;
            try {
                Age2InstallEngine.Install(package,game,profile,line=>{
                    if(line.StartsWith("正在安装"))locked=new FileStream(Path.Combine(game,"age2-cn.js"),FileMode.Open,FileAccess.Read,FileShare.None);
                });
            }catch(IOException e){rolledBack=e.Message.Contains("已恢复安装前状态");}
            finally {if(locked!=null)locked.Dispose();}
            Assert(rolledBack,"Interrupted install did not roll back");
            Assert(Age2InstallEngine.Hash(File.ReadAllBytes(exe))==m.native.patched_sha256,"Rollback altered executable");
            Assert(File.ReadAllText(user)=="PLAYER-SAVE","Rollback changed player save");
            foreach(var entry in m.files.Where(f=>f.path.StartsWith("root/")))Assert(Age2InstallEngine.Hash(File.ReadAllBytes(Age2InstallEngine.Child(root,entry.path.Substring(5))))==entry.sha256,"Rollback lost active resource");
            foreach(string bad in new[]{"../outside","C:/outside","a/../b","a:stream","a/./b","a/"}) {
                rejected=false;try {Age2InstallEngine.Child(root,bad);}catch(IOException){rejected=true;}Assert(rejected,"Unsafe relative path accepted");
            }
            Console.WriteLine("PASS: install, reinstall, retained originals, save preservation, corrupt payload, wrong version, commit rollback, unsafe paths.");
            return 0;
        }catch(Exception error){Console.Error.WriteLine(error);return 1;}
    }
}
