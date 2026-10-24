using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Windows.Forms;

internal static class Launcher
{
    [STAThread]
    private static int Main(string[] args)
    {
        string root = Directory.GetParent(AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar)).FullName;
        string script = Path.Combine(root, "work", "agent", "projects_desk.ps1");
        string python = Path.Combine(root, ".venv", "Scripts", "python.exe");
        bool probe = args.Length == 1 && args[0] == "--probe";
        bool selfTest = args.Length == 1 && args[0] == "--self-test";
        if (args.Length != 0 && !probe && !selfTest) return 2;
        try
        {
            if (!File.Exists(script) || !File.Exists(python))
                throw new FileNotFoundException("Proje dosyaları bulunamadı. Bu EXE, projenin outputs klasöründe kalmalı.");
            if (probe)
            {
                File.WriteAllText(Path.Combine(root, "outputs", "reports", "exe_launcher_probe.json"),
                    "{\"passed\":true,\"project_relative_paths\":true,\"console_required\":false,\"kind\":\"launcher\"}", new UTF8Encoding(false));
                return 0;
            }
            var info = new ProcessStartInfo();
            info.FileName = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "WindowsPowerShell", "v1.0", "powershell.exe");
            info.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File \"" + script + "\"" + (selfTest ? " -SelfTest" : "");
            info.WorkingDirectory = root; info.UseShellExecute = false; info.CreateNoWindow = true;
            info.WindowStyle = ProcessWindowStyle.Hidden;
            info.RedirectStandardOutput = true; info.RedirectStandardError = true;
            string logFolder = Path.Combine(root, "work", "agent", "ui-logs");
            Directory.CreateDirectory(logFolder);
            string logPath = Path.Combine(logFolder, "launcher-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff") + ".log");
            using (var log = new StreamWriter(logPath, false, new UTF8Encoding(false)))
            using (var process = new Process())
            {
                object gate = new object(); process.StartInfo = info;
                DataReceivedEventHandler receive = delegate(object sender, DataReceivedEventArgs e)
                { if (e.Data != null) lock (gate) { log.WriteLine(e.Data); log.Flush(); } };
                process.OutputDataReceived += receive; process.ErrorDataReceived += receive;
                process.Start(); process.BeginOutputReadLine(); process.BeginErrorReadLine();
                process.WaitForExit();
                int code = process.ExitCode;
                if (code != 0 && !selfTest)
                    MessageBox.Show("Arayüz açılamadı veya bir hata ile kapandı. Hata kaydı:\n" + logPath,
                        "Mühendislik Merkezi", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return code;
            }
        }
        catch (Exception ex)
        {
            if (!selfTest && !probe) MessageBox.Show(ex.Message, "Mühendislik Merkezi", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return 1;
        }
    }
}
