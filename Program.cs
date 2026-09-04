using System.Runtime.InteropServices;

namespace Mindtorio;

internal class Program
{
    [DllImport("kernel32.dll")]
    private static extern IntPtr GetConsoleWindow();

    [DllImport("user32.dll")]
    private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    static void Main(string[] args)
    {

    #if DEBUG
                Console.WriteLine("Debug Build!");
    #endif

    #if !DEBUG
        ShowWindow(GetConsoleWindow(), 0);  // Скрыть консоль
    #endif

        MainGame game = new();
        
    }
}

