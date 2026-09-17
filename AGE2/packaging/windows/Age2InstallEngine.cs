using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;

// Used by the per-game Windows installer. All game data is version checked
// before mutation; previous loose resources remain in a recoverable archive.
public sealed class Age2PackageFile { public string path; public long size; public string sha256; }
public sealed class Age2Native { public string original_sha256; public string patched_sha256; }
public sealed class Age2Manifest {
    public string format, game, title, version, exe;
    public Age2Native native;
    public Age2PackageFile[] files;
    public string[] foundation;
}
public sealed class Age2Edit { public int offset; public string data; }
public sealed class Age2Delta {
    public string format, original_sha256, patched_sha256;
    public int output_size;
    public Age2Edit[] edits;
}
public static class Age2InstallEngine {
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = 64 * 1024 * 1024 };
    static readonly string[] Games = { "tm", "tda00", "tda01", "tda02", "tda03" };
    static readonly string[] RuntimeFiles = { "FridaGadget.dll", "FridaGadget.config", "COPYING-frida.txt", "age2-cn.js" };
    static readonly string[] Foundation = { "readme.txt", "resident.list", "data/hiscore.conf" };
    public static string Hash(byte[] data) {
        using (var sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(data)).Replace("-", "").ToLowerInvariant();
    }
    static T ReadJson<T>(string path) { return Json.Deserialize<T>(File.ReadAllText(path, Encoding.UTF8)); }
    static void WriteJson(string path, object value) { File.WriteAllText(path, Json.Serialize(value), new UTF8Encoding(false)); }
    public static string Child(string root, string relative) {
        if (String.IsNullOrWhiteSpace(relative) || Path.IsPathRooted(relative) || relative.Contains(":")) throw new IOException("补丁含无效路径。");
        var parts = relative.Replace('\\', '/').Split('/');
        if (parts.Any(p => p.Length == 0 || p == "." || p == ".." || p.EndsWith(".") || p.EndsWith(" "))) throw new IOException("补丁含无效路径。");
        string prefix = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        string path = Path.GetFullPath(Path.Combine(prefix, relative.Replace('/', Path.DirectorySeparatorChar)));
        if (!path.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)) throw new IOException("补丁路径超出安装目录。");
        return path;
    }
    public static void NoLinks(string path, bool tree) {
        string current = Path.GetFullPath(path);
        while (current != null) {
            if ((File.Exists(current) || Directory.Exists(current)) && (File.GetAttributes(current) & FileAttributes.ReparsePoint) != 0)
                throw new IOException("目录包含链接，请选择实际目录：" + current);
            current = Path.GetDirectoryName(current);
        }
        if (!tree || !Directory.Exists(path)) return;
        foreach (var item in Directory.EnumerateFileSystemEntries(path)) {
            if ((File.GetAttributes(item) & FileAttributes.ReparsePoint) != 0) throw new IOException("资源目录包含链接：" + item);
            if (Directory.Exists(item)) NoLinks(item, true);
        }
    }
    public static Age2Manifest Verify(string package) {
        NoLinks(package, true);
        var manifest = ReadJson<Age2Manifest>(Child(package, "manifest.json"));
        if (manifest.format != "age2-cn-package-1" || !Games.Contains(manifest.game) || manifest.exe != manifest.game + "-win64vc14-release.exe")
            throw new IOException("补丁作品信息无效。");
        if (manifest.files == null || manifest.files.Length == 0 || manifest.native == null || manifest.foundation == null ||
            !new HashSet<string>(manifest.foundation).SetEquals(Foundation)) throw new IOException("补丁清单不完整。");
        var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var entry in manifest.files) {
            if (entry == null || entry.path == null || !names.Add(entry.path)) throw new IOException("补丁含重复资源。");
            if (!entry.path.StartsWith("root/", StringComparison.Ordinal) && !RuntimeFiles.Select(f => "game/" + f).Contains(entry.path))
                throw new IOException("补丁含未知安装目标。");
            string file = Child(package, entry.path);
            if (!File.Exists(file) || new FileInfo(file).Length != entry.size || Hash(File.ReadAllBytes(file)) != entry.sha256)
                throw new IOException("补丁文件损坏：" + entry.path);
        }
        if (Foundation.Any(f => !names.Contains("root/" + f)) || RuntimeFiles.Any(f => !names.Contains("game/" + f))) throw new IOException("补丁基础文件缺失。");
        var delta = ReadJson<Age2Delta>(Child(package, "exe.delta.json"));
        if (delta.original_sha256 != manifest.native.original_sha256 || delta.patched_sha256 != manifest.native.patched_sha256)
            throw new IOException("程序差分与补丁清单不一致。");
        return manifest;
    }
    public static byte[] ApplyDelta(byte[] original, Age2Delta delta) {
        if (delta.format != "age2-exe-delta-1" || Hash(original) != delta.original_sha256 || delta.output_size < 1 || delta.output_size > 256 * 1024 * 1024 || delta.edits == null)
            throw new IOException("游戏版本不符合补丁要求。");
        byte[] result = new byte[delta.output_size];
        Buffer.BlockCopy(original, 0, result, 0, Math.Min(original.Length, result.Length));
        long previousEnd = 0;
        foreach (var edit in delta.edits) {
            byte[] bytes = Convert.FromBase64String(edit.data);
            if (edit.offset < previousEnd || (long)edit.offset + bytes.Length > result.Length) throw new IOException("程序差分范围无效。");
            Buffer.BlockCopy(bytes, 0, result, edit.offset, bytes.Length); previousEnd = (long)edit.offset + bytes.Length;
        }
        if (Hash(result) != delta.patched_sha256) throw new IOException("程序差分校验失败。");
        return result;
    }
    static void CopyFile(string source, string target) {
        Directory.CreateDirectory(Path.GetDirectoryName(target)); File.Copy(source, target, false);
    }
    static void RequireStopped(string exe) {
        if (Process.GetProcessesByName(Path.GetFileNameWithoutExtension(exe)).Length != 0) throw new IOException("请先退出游戏，再安装补丁。");
        using (var stream = new FileStream(exe, FileMode.Open, FileAccess.Read, FileShare.None)) { }
    }
    // localAppData is supplied by the UI from the Windows known folder, not
    // inferred from a Steam path. Tests use an explicitly isolated directory.
    public static string Install(string package, string gameRoot, string localAppData, Action<string> report) {
        if (report == null) report = delegate { };
        report("正在检查补丁与游戏版本…");
        var m = Verify(package);
        gameRoot = Path.GetFullPath(gameRoot); localAppData = Path.GetFullPath(localAppData);
        string exe = Child(gameRoot, m.exe), storage = Child(gameRoot, ".age2-cn"), savedExe = Child(storage, "original.exe");
        string data = Child(localAppData, "ancr/" + m.game + "/data"), root = Child(data, "root");
        NoLinks(gameRoot, false); NoLinks(storage, true); NoLinks(data, false); NoLinks(root, true);
        if (!File.Exists(exe)) throw new IOException("所选目录没有对应游戏程序。");
        RequireStopped(exe);
        byte[] current = File.ReadAllBytes(exe), original;
        if (Hash(current) == m.native.original_sha256) original = current;
        else if (Hash(current) == m.native.patched_sha256 && File.Exists(savedExe) && Hash(File.ReadAllBytes(savedExe)) == m.native.original_sha256) original = File.ReadAllBytes(savedExe);
        else throw new IOException("游戏程序版本不匹配。请通过 Steam 验证游戏文件后重试。");
        if (File.Exists(savedExe) && Hash(File.ReadAllBytes(savedExe)) != m.native.original_sha256) throw new IOException("保存的原版程序校验失败，已停止安装。");
        foreach (string name in RuntimeFiles) {
            string path = Child(gameRoot, name); NoLinks(path, false);
            if (File.Exists(path) && !File.Exists(savedExe)) throw new IOException("游戏目录已有同名运行组件，请先确认来源：" + name);
        }
        foreach (var entry in m.files.Where(f => f.path.StartsWith("root/")))
            if (Child(root, entry.path.Substring(5)).Length >= 256) throw new IOException("本机用户数据路径过长，游戏无法读取部分资源。");
        byte[] patched = ApplyDelta(original, ReadJson<Age2Delta>(Child(package, "exe.delta.json")));
        string id = DateTime.UtcNow.ToString("yyyyMMddHHmmss") + "-" + Guid.NewGuid().ToString("N").Substring(0, 8);
        string work = Child(storage, "transactions/" + id), dataWork = Child(data, ".age2-cn-work/" + id);
        string newRoot = Child(dataWork, "root"), oldRoot = Child(data, ".age2-cn-backups/" + id + "/root");
        NoLinks(Path.GetDirectoryName(oldRoot), false); NoLinks(dataWork, false);
        Directory.CreateDirectory(work); Directory.CreateDirectory(newRoot);
        report("正在准备独立中文资源…");
        foreach (var entry in m.files.Where(f => f.path.StartsWith("root/"))) CopyFile(Child(package, entry.path), Child(newRoot, entry.path.Substring(5)));
        var targets = RuntimeFiles.Concat(new[] { m.exe }).ToArray();
        foreach (string name in RuntimeFiles) CopyFile(Child(package, "game/" + name), Child(work, "new/" + name));
        File.WriteAllBytes(Child(work, "new/" + m.exe), patched);
        if (!File.Exists(savedExe)) CopyFile(exe, savedExe);
        // Finish every check and copy before removing anything from active use.
        RequireStopped(exe); NoLinks(root, true);
        var movedOld = new List<string>(); var installed = new List<string>();
        bool archivedRoot = false, activatedRoot = false;
        try {
            report("正在安装，并保留旧资源副本…");
            if (Directory.Exists(root)) { Directory.CreateDirectory(Path.GetDirectoryName(oldRoot)); Directory.Move(root, oldRoot); archivedRoot = true; }
            Directory.Move(newRoot, root); activatedRoot = true;
            foreach (string name in targets) {
                string dest = Child(gameRoot, name), previous = Child(work, "old/" + name);
                if (File.Exists(dest)) { Directory.CreateDirectory(Path.GetDirectoryName(previous)); File.Move(dest, previous); movedOld.Add(name); }
                File.Move(Child(work, "new/" + name), dest); installed.Add(name);
            }
            WriteJson(Child(work, "receipt.json"), new { game = m.game, version = m.version, gameRoot, dataRoot = root, previousRoot = archivedRoot ? oldRoot : null, originalExe = savedExe, installed = targets, status = "installed" });
            report("安装完成。旧资源已保留，存档目录未改动。");
            return Child(work, "receipt.json");
        } catch (Exception error) {
            // Move only this transaction's files; keep failed outputs for
            // diagnosis rather than deleting an unknown or newly changed file.
            try {
                foreach (string name in installed.AsEnumerable().Reverse()) { string dest = Child(work, "failed/" + name); Directory.CreateDirectory(Path.GetDirectoryName(dest)); File.Move(Child(gameRoot, name), dest); }
                foreach (string name in movedOld.AsEnumerable().Reverse()) File.Move(Child(work, "old/" + name), Child(gameRoot, name));
                if (activatedRoot) Directory.Move(root, Child(dataWork, "failed-root"));
                if (archivedRoot) Directory.Move(oldRoot, root);
                WriteJson(Child(work, "receipt.json"), new { status = "rolled-back", error = error.Message });
            } catch (Exception rollback) { throw new IOException("安装中断且自动恢复未完成。请保留此目录以便恢复：" + work + "\n" + rollback.Message, error); }
            throw new IOException("安装未完成，已恢复安装前状态。" + error.Message, error);
        }
    }
}
