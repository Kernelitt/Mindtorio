using ImGuiNET;
using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;
using OpenTK.Windowing.Desktop;
using OpenTK.Windowing.GraphicsLibraryFramework;
namespace Mindtorio.Framework;
public class ImGuiController : IDisposable
{
    private int _fontTexture;
    private int _shaderProgram;
    private int _vbo, _ebo, _vao;
    private int _windowWidth;
    private int _windowHeight;
    private System.Numerics.Vector2 _scaleFactor = System.Numerics.Vector2.One;

    public ImGuiController(int width, int height)
    {
        _windowWidth = width;
        _windowHeight = height;

        // 1. Создаем контекст ImGui
        IntPtr context = ImGui.CreateContext();
        ImGui.SetCurrentContext(context);

        var io = ImGui.GetIO();
        io.ConfigFlags |= ImGuiConfigFlags.DockingEnable; // Включаем докинг окон по желанию

        // 2. Инициализируем графические ресурсы
        InitGeometry();
        InitShaders();
        CreateFontTexture();


        // Настройка стиля
        ImGui.StyleColorsDark();
    }

    public void WindowResized(int width, int height)
    {
        _windowWidth = width;
        _windowHeight = height;
    }

    public void Update(GameWindow window, float deltaTime)
    {
        var io = ImGui.GetIO();
        io.DeltaTime = deltaTime;
        io.DisplaySize = new System.Numerics.Vector2(_windowWidth, _windowHeight);
        io.DisplayFramebufferScale = _scaleFactor;

        // Обновляем ввод мыши
        var mouseState = window.MouseState;
        io.MousePos = new System.Numerics.Vector2(mouseState.X, mouseState.Y);
        io.MouseDown[0] = mouseState.IsButtonDown(MouseButton.Left);
        io.MouseDown[1] = mouseState.IsButtonDown(MouseButton.Right);
        io.MouseDown[2] = mouseState.IsButtonDown(MouseButton.Middle);

        ImGui.NewFrame();
    }

    public void Render()
    {
        ImGui.Render();
        RenderDrawData(ImGui.GetDrawData());
    }

    private void RenderDrawData(ImDrawDataPtr drawData)
    {
        if (drawData.CmdListsCount == 0) return;

        // Сохраняем состояние OpenGL State перед отрисовкой UI
        int[] lastViewport = new int[4];
        GL.GetInteger(GetPName.Viewport, lastViewport);
        GL.Enable(EnableCap.Blend);
        GL.BlendEquation(BlendEquationMode.FuncAdd);
        GL.BlendFunc(BlendingFactor.SrcAlpha, BlendingFactor.OneMinusSrcAlpha);
        GL.Disable(EnableCap.CullFace);
        GL.Disable(EnableCap.DepthTest);
        GL.Enable(EnableCap.ScissorTest);

        // Настраиваем ортографическую матрицу
        GL.UseProgram(_shaderProgram);
        var io = ImGui.GetIO();
        Matrix4 mvp = Matrix4.CreateOrthographicOffCenter(0.0f, io.DisplaySize.X, io.DisplaySize.Y, 0.0f, -1.0f, 1.0f);
        GL.UniformMatrix4(GL.GetUniformLocation(_shaderProgram, "projection_matrix"), false, ref mvp);

        GL.BindVertexArray(_vao);

        for (int n = 0; n < drawData.CmdListsCount; n++)
        {
            ImDrawListPtr cmdList = drawData.CmdLists[n];

            // Загружаем вершины и индексы в GPU
            GL.BindBuffer(BufferTarget.ArrayBuffer, _vbo);
            GL.BufferData(BufferTarget.ArrayBuffer, cmdList.VtxBuffer.Size * UnsafeSizeOf<ImDrawVert>(), cmdList.VtxBuffer.Data, BufferUsageHint.StreamDraw);

            GL.BindBuffer(BufferTarget.ElementArrayBuffer, _ebo);
            GL.BufferData(BufferTarget.ElementArrayBuffer, cmdList.IdxBuffer.Size * sizeof(ushort), cmdList.IdxBuffer.Data, BufferUsageHint.StreamDraw);

            for (int cmdIdx = 0; cmdIdx < cmdList.CmdBuffer.Size; cmdIdx++)
            {
                ImDrawCmdPtr pcmd = cmdList.CmdBuffer[cmdIdx];

                // Проекция Scissor (отсечение текста/кнопок за пределами окон)
                GL.Scissor((int)pcmd.ClipRect.X, _windowHeight - (int)pcmd.ClipRect.W, (int)(pcmd.ClipRect.Z - pcmd.ClipRect.X), (int)(pcmd.ClipRect.W - pcmd.ClipRect.Y));

                GL.BindTexture(TextureTarget.Texture2D, (int)pcmd.TextureId);
                GL.DrawElements(BeginMode.Triangles, (int)pcmd.ElemCount, DrawElementsType.UnsignedShort, (int)(pcmd.IdxOffset * sizeof(ushort)));
            }
        }

        // Восстанавливаем состояние OpenGL
        GL.Disable(EnableCap.ScissorTest);
        GL.Enable(EnableCap.DepthTest);
        GL.Viewport(lastViewport[0], lastViewport[1], lastViewport[2], lastViewport[3]);
    }

    private void CreateFontTexture()
    {
        var io = ImGui.GetIO();
        io.Fonts.GetTexDataAsRGBA32(out IntPtr pixels, out int width, out int height);

        _fontTexture = GL.GenTexture();
        GL.BindTexture(TextureTarget.Texture2D, _fontTexture);
        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMinFilter, (int)TextureMinFilter.Linear);
        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMagFilter, (int)TextureMagFilter.Linear);
        GL.TexImage2D(TextureTarget.Texture2D, 0, PixelInternalFormat.Rgba, width, height, 0, PixelFormat.Rgba, PixelType.UnsignedByte, pixels);

        io.Fonts.SetTexID((IntPtr)_fontTexture);
        io.Fonts.ClearTexData();
    }

    private void InitGeometry()
    {
        _vao = GL.GenVertexArray();
        _vbo = GL.GenBuffer();
        _ebo = GL.GenBuffer();

        GL.BindVertexArray(_vao);
        GL.BindBuffer(BufferTarget.ArrayBuffer, _vbo);

        int stride = UnsafeSizeOf<ImDrawVert>();
        // Позиция
        GL.EnableVertexAttribArray(0);
        GL.VertexAttribPointer(0, 2, VertexAttribPointerType.Float, false, stride, 0);
        // Текстурные координаты
        GL.EnableVertexAttribArray(1);
        GL.VertexAttribPointer(1, 2, VertexAttribPointerType.Float, false, stride, 8);
        // Цвет
        GL.EnableVertexAttribArray(2);
        GL.VertexAttribPointer(2, 4, VertexAttribPointerType.UnsignedByte, true, stride, 16);
    }

    private void InitShaders()
    {
        string vertexShaderSource = @"#version 330 core
        layout (location = 0) in vec2 Position;
        layout (location = 1) in vec2 UV;
        layout (location = 2) in vec4 Color;
        uniform mat4 projection_matrix;
        out vec2 Frag_UV;
        out vec4 Frag_Color;
        void main() {
            Frag_UV = UV;
            Frag_Color = Color;
            gl_Position = projection_matrix * vec4(Position.xy, 0, 1);
        }";

        string fragmentShaderSource = @"#version 330 core
        in vec2 Frag_UV;
        in vec4 Frag_Color;
        uniform sampler2D Texture;
        layout (location = 0) out vec4 Out_Color;
        void main() {
            Out_Color = Frag_Color * texture(Texture, Frag_UV.st);
        }";

        int vs = GL.CreateShader(ShaderType.VertexShader);
        GL.ShaderSource(vs, vertexShaderSource);
        GL.CompileShader(vs);

        int fs = GL.CreateShader(ShaderType.FragmentShader);
        GL.ShaderSource(fs, fragmentShaderSource);
        GL.CompileShader(fs);

        _shaderProgram = GL.CreateProgram();
        GL.AttachShader(_shaderProgram, vs);
        GL.AttachShader(_shaderProgram, fs);
        GL.LinkProgram(_shaderProgram);

        GL.DeleteShader(vs);
        GL.DeleteShader(fs);
    }

    public static void PressChar(char c)
    {
        ImGui.GetIO().AddInputCharacter(c);
    }

    private static unsafe int UnsafeSizeOf<T>() where T : unmanaged => sizeof(T);

    public void Dispose()
    {
        GL.DeleteBuffer(_vbo);
        GL.DeleteBuffer(_ebo);
        GL.DeleteVertexArray(_vao);
        GL.DeleteTexture(_fontTexture);
        GL.DeleteProgram(_shaderProgram);
        ImGui.DestroyContext();
    }
}
