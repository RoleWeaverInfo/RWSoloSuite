using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;

[assembly: AssemblyTitle("Role Weaver Module Studio")]
[assembly: AssemblyCompany("RoleWeaverInfo")]
[assembly: AssemblyProduct("Role Weaver Module Studio")]
[assembly: AssemblyVersion("0.20.0.2")]

internal static class ServiceLauncher
{
    // Quote for Windows CommandLineToArgvW, including trailing backslashes.
    private static string Quote(string value)
    {
        var result = new StringBuilder("\"");
        int slashes = 0;
        foreach (char character in value)
        {
            if (character == '\\') { slashes++; continue; }
            result.Append('\\', character == '"' ? slashes * 2 + 1 : slashes);
            result.Append(character);
            slashes = 0;
        }
        result.Append('\\', slashes * 2);
        return result.Append('"').ToString();
    }

    private static int Main(string[] args)
    {
        try
        {
            Console.Title = "Role Weaver Service";
            string root = AppDomain.CurrentDomain.BaseDirectory;
            string python = Path.Combine(root, "runtime", "python.exe");
            string script = Path.Combine(root, "service.py");
            if (!File.Exists(python) || !File.Exists(script))
                throw new FileNotFoundException("Role Weaver's bundled runtime is missing. Run Setup again to repair the installation.");
            var command = new StringBuilder("-B ").Append(Quote(script));
            foreach (string arg in args) command.Append(' ').Append(Quote(arg));
            var start = new ProcessStartInfo(python, command.ToString());
            start.WorkingDirectory = root;
            start.UseShellExecute = false;
            using (var process = Process.Start(start))
            {
                process.WaitForExit();
                if (process.ExitCode != 0 && !Console.IsInputRedirected)
                {
                    Console.Error.WriteLine("Press a key to close this window.");
                    Console.ReadKey(true);
                }
                return process.ExitCode;
            }
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("Cannot start Role Weaver: " + error.Message);
            if (!Console.IsInputRedirected) Console.ReadKey(true);
            return 1;
        }
    }
}
