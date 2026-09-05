using Mindtorio.Framework;
using OpenTK.Windowing.Common;
using OpenTK.Windowing.Desktop;

namespace Mindtorio
{
    internal class MainGame
    {
        GLRenderer glRenderer = new GLRenderer(
            GameWindowSettings.Default,
            new NativeWindowSettings()
            {
                Title = "Mindtorio",
                ClientSize = (1600,900),
                APIVersion = new System.Version(4,6),
                AspectRatio = (16,9),
                Flags = ContextFlags.ForwardCompatible,
                Profile = ContextProfile.Core,
                Vsync = VSyncMode.On,
                DepthBits = 24
            }

            );
        public MainGame() 
        {
            glRenderer.Run();
        }
    }
}
