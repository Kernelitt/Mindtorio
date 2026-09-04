using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;
using OpenTK.Windowing.Common;
using OpenTK.Windowing.Desktop;
using OpenTK.Windowing.GraphicsLibraryFramework;

namespace Mindtorio.Framework
{
    public class GLRenderer(GameWindowSettings gameWindowSettings, NativeWindowSettings nativeWindowSettings) : GameWindow(gameWindowSettings, nativeWindowSettings)
    {
        private Shader _shader;
        private ObjMesh? _objMesh;
        private bool _useObj = true; // переключатель: куб или obj

        // Камера
        private Camera _camera;

        private bool _firstMove = true;
        private float _lastX;
        private float _lastY;

        private Matrix4 _projection;

        // Свет
        private Vector3 _lightDir;
        private Vector3 _lightColor;
        private Vector3 _ambient;
        private Vector3 _objectColor;

        private ChunkManager _chunkManager;

        private Matrix4 _lightSpaceMatrix;
        private int _objVao;
        private int _objVboPos;
        private int _objVboNorm;
        private int _objEbo;
        private int _objTex;
        private static void CreateMeshVao(IMeshData mesh, out int vao, out int vboPos, out int vboNorm, out int ebo, out int vboTex)
        {
            vao = GL.GenVertexArray();
            GL.BindVertexArray(vao);

            // Позиции (location 0)
            vboPos = GL.GenBuffer();
            GL.BindBuffer(BufferTarget.ArrayBuffer, vboPos);
            GL.BufferData(BufferTarget.ArrayBuffer, mesh.Positions.Length * sizeof(float), mesh.Positions, BufferUsageHint.StaticDraw);
            GL.VertexAttribPointer(0, 3, VertexAttribPointerType.Float, false, 3 * sizeof(float), 0);
            GL.EnableVertexAttribArray(0);

            // Нормали (location 1)
            vboNorm = GL.GenBuffer();
            GL.BindBuffer(BufferTarget.ArrayBuffer, vboNorm);
            GL.BufferData(BufferTarget.ArrayBuffer, mesh.Normals.Length * sizeof(float), mesh.Normals, BufferUsageHint.StaticDraw);
            GL.VertexAttribPointer(1, 3, VertexAttribPointerType.Float, false, 3 * sizeof(float), 0);
            GL.EnableVertexAttribArray(1);

            // UV (location 2) ✅
            try
            {
                vboTex = GL.GenBuffer();
                GL.BindBuffer(BufferTarget.ArrayBuffer, vboTex);
                GL.BufferData(BufferTarget.ArrayBuffer, mesh.TexCoords.Length * sizeof(float), mesh.TexCoords, BufferUsageHint.StaticDraw);
                GL.VertexAttribPointer(2, 2, VertexAttribPointerType.Float, false, 2 * sizeof(float), 0);
                GL.EnableVertexAttribArray(2);
            }
            catch
            {
                vboTex = -1;
            }

            // Индексы
            ebo = GL.GenBuffer();
            GL.BindBuffer(BufferTarget.ElementArrayBuffer, ebo);
            GL.BufferData(BufferTarget.ElementArrayBuffer, mesh.Indices.Length * sizeof(uint), mesh.Indices, BufferUsageHint.StaticDraw);

            GL.BindBuffer(BufferTarget.ArrayBuffer, 0);
            GL.BindVertexArray(0);
        }

        protected override void OnLoad()
        {
            base.OnLoad();

            GL.ClearColor(0.21f, 0.24f, 0.7f, 1.0f);
            GL.Enable(EnableCap.DepthTest);

            _shader = new Shader("Shaders/shader.vert", "Shaders/shader.frag");

            _objMesh = new ObjMesh("Models/metallicTest.obj"); // или любой другой .obj
            _useObj = true;
            if (_useObj && _objMesh != null)
            {
                CreateMeshVao(_objMesh, out _objVao, out _objVboPos, out _objVboNorm, out _objEbo, out _objTex);
            }

            _chunkManager = new ChunkManager(
                chunkSize: 128,
                chunkQuality: 1024,
                heightScale: 128f,
                noiseSeed: 1124
            );



            // Камера
            _camera = new Camera(
                position: new Vector3(0f, 2f, 5f),
                yaw: -90f,
                pitch: 0f,
                movementSpeed: 400f,
                mouseSensitivity: 0.15f
            );

            float aspect = ClientSize.X / (float)ClientSize.Y;
            float fov = MathHelper.DegreesToRadians(70f);
            float near = 0.1f;
            float far = 5000f;
            _projection = Matrix4.CreatePerspectiveFieldOfView(fov, aspect, near, far);

            // Свет
            _lightDir = new Vector3(1f, 0.4f, 1f); 
            _lightColor = new Vector3(0.9f, 0.9f, 0.9f);
            _ambient = new Vector3(0.2f, 0.2f, 0.2f);
            _objectColor = new Vector3(1f, 0.5f, 0.2f);


            CursorState = CursorState.Hidden;
            MousePosition = new Vector2(ClientSize.X / 2f, ClientSize.Y / 2f);
        }

        protected override void OnUnload()
        {
            base.OnUnload();
        }

        protected override void OnMouseMove(MouseMoveEventArgs e)
        {
            base.OnMouseMove(e);

            if (_firstMove)
            {
                _lastX = e.X;
                _lastY = e.Y;
                _firstMove = false;
                return;
            }

            float deltaX = e.X - _lastX;
            float deltaY = e.Y - _lastY;

            _lastX = ClientSize.X / 2f;
            _lastY = ClientSize.Y / 2f;

            _camera.ProcessMouseMovement(deltaX, deltaY);
            MousePosition = new Vector2(ClientSize.X / 2f, ClientSize.Y / 2f);
        }

        protected override void OnResize(ResizeEventArgs e)
        {
            base.OnResize(e);

            float aspect = ClientSize.X / (float)ClientSize.Y;
            float fov = MathHelper.DegreesToRadians(70f);
            float near = 0.1f;
            float far = 5000f;
            _projection = Matrix4.CreatePerspectiveFieldOfView(fov, aspect, near, far);
        }

        protected override void OnFramebufferResize(FramebufferResizeEventArgs e)
        {
            base.OnFramebufferResize(e);
            GL.Viewport(0, 0, e.Width, e.Height);
        }

        protected override void OnUpdateFrame(FrameEventArgs e)
        {
            base.OnUpdateFrame(e);

            if (KeyboardState.IsKeyDown(Keys.Escape))
            {
                Close();
            }
            if (KeyboardState.IsKeyDown(Keys.W))
                _camera.ProcessKeyboard(CameraMovement.Forward, (float)e.Time);
            if (KeyboardState.IsKeyDown(Keys.S))
                _camera.ProcessKeyboard(CameraMovement.Backward, (float)e.Time);
            if (KeyboardState.IsKeyDown(Keys.A))
                _camera.ProcessKeyboard(CameraMovement.Left, (float)e.Time);
            if (KeyboardState.IsKeyDown(Keys.D))
                _camera.ProcessKeyboard(CameraMovement.Right, (float)e.Time);
            if (KeyboardState.IsKeyDown(Keys.E))
                _camera.ProcessKeyboard(CameraMovement.Up, (float)e.Time);
            if (KeyboardState.IsKeyDown(Keys.Q))
                _camera.ProcessKeyboard(CameraMovement.Down, (float)e.Time);

            _chunkManager.Update(_camera.Position, renderDistance: 3);


        }

        protected override void OnRenderFrame(FrameEventArgs e)
        {
            base.OnRenderFrame(e);

            GL.Viewport(0, 0, ClientSize.X, ClientSize.Y);
            GL.Clear(ClearBufferMask.ColorBufferBit | ClearBufferMask.DepthBufferBit);

            _shader.Use();
            _shader.SetVector3("uCameraPos", _camera.Position);
            // Привязка shadow map
            GL.ActiveTexture(TextureUnit.Texture0);
            _shader.SetMatrix4("uLightSpace", _lightSpaceMatrix);

            // Terrain
            _shader.SetFloat("uObjectReflectPower", 0.15f); 
            _shader.SetInt("uTerrainTexture", 0); //_sampler2D = texture unit 0
            _shader.SetInt("uUseTerrainTexture", 1); // включаем текстуру

            _shader.SetMatrix4("uView", _camera.GetViewMatrix());
            _shader.SetMatrix4("uProjection", _projection);

            _shader.SetVector3("uLightDir", _lightDir);
            _shader.SetVector3("uLightColor", _lightColor);
            _shader.SetVector3("uAmbient", _ambient);

            _chunkManager.Render(_shader, _camera.GetViewMatrix(), _projection);
            _shader.SetInt("uUseTerrainTexture", 0);
            // Obj 
            GL.BindVertexArray(_objVao);
            _shader.SetMatrix4("uModel", Matrix4.Identity);
            _shader.SetVector3("uObjectColor", _objectColor);
            _shader.SetFloat("uObjectReflectPower", 1.0f);
            GL.DrawElements(PrimitiveType.Triangles, _objMesh.Indices.Length, DrawElementsType.UnsignedInt, 0);
            GL.BindVertexArray(0);

            SwapBuffers();
        }
    }
}