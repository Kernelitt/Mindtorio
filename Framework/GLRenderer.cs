using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;
using OpenTK.Windowing.Common;
using OpenTK.Windowing.Desktop;
using OpenTK.Windowing.GraphicsLibraryFramework;
using ImGuiNET;

namespace Mindtorio.Framework
{
    public class GLRenderer(GameWindowSettings gameWindowSettings, NativeWindowSettings nativeWindowSettings) : GameWindow(gameWindowSettings, nativeWindowSettings)
    {
        private Shader _shader;
        private ObjMesh? _objMesh;

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

        private int _fieldOfView = 60, drawDistance = 3000, chunkRenderDistance = 3;

        private bool isMouseFixed = true;

        private ImGuiController _guiController;
        private int seed = 0;

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
            if (_objMesh != null)
            {
                CreateMeshVao(_objMesh, out _objVao, out _objVboPos, out _objVboNorm, out _objEbo, out _objTex);
            }

            _chunkManager = new ChunkManager(
                chunkSize: 256,
                chunkQuality: 2048,
                heightScale: 256f,
                noiseSeed: 0
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
            float far = 1000f;
            _projection = Matrix4.CreatePerspectiveFieldOfView(fov, aspect, near, far);

            // Свет
            _lightDir = new Vector3(1f, 0.4f, 1f); 
            _lightColor = new Vector3(0.9f, 0.9f, 0.9f);
            _ambient = new Vector3(0.2f, 0.2f, 0.2f);
            _objectColor = new Vector3(1f, 0.5f, 0.2f);

            _guiController = new ImGuiController(ClientSize.X, ClientSize.Y);

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

            if (isMouseFixed)
            {
                float deltaX = e.X - _lastX;
                float deltaY = e.Y - _lastY;

                _lastX = ClientSize.X / 2f;
                _lastY = ClientSize.Y / 2f;

                _camera.ProcessMouseMovement(deltaX, deltaY);
                CursorState = CursorState.Hidden;
                MousePosition = new Vector2(ClientSize.X / 2f, ClientSize.Y / 2f);
            }
            else
            {
                CursorState = CursorState.Normal;
            }
        }

        protected override void OnResize(ResizeEventArgs e)
        {
            base.OnResize(e);

            float aspect = ClientSize.X / (float)ClientSize.Y;
            float fov = MathHelper.DegreesToRadians(70f);
            float near = 0.1f;
            float far = 5000f;
            _projection = Matrix4.CreatePerspectiveFieldOfView(fov, aspect, near, far);

            _guiController.WindowResized(e.Width, e.Height);
        }

        protected override void OnFramebufferResize(FramebufferResizeEventArgs e)
        {
            base.OnFramebufferResize(e);
            GL.Viewport(0, 0, e.Width, e.Height);
        }

        protected override void OnUpdateFrame(FrameEventArgs e)
        {
            base.OnUpdateFrame(e);


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
            if (KeyboardState.IsKeyPressed(Keys.Escape))
               isMouseFixed = !isMouseFixed;

            _chunkManager.Update(_camera.Position, renderDistance: chunkRenderDistance);


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

            _shader.SetFloat("uObjectReflectPower", 0.25f); 
            _shader.SetInt("uTerrainTexture", 0); 
            _shader.SetInt("uUseTerrainTexture", 1); 

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
            _shader.SetFloat("uObjectReflectPower", 3.0f);
            GL.DrawElements(PrimitiveType.Triangles, _objMesh.Indices.Length, DrawElementsType.UnsignedInt, 0);
            GL.BindVertexArray(0);

            // Начинаем сборку интерфейса
            _guiController.Update(this, (float)e.Time);

            ImGui.Begin("Debug Menu");
            ImGui.SetWindowSize(new System.Numerics.Vector2(400f,300f));

            ImGui.Text("Press Esc to Lock/Release cursor");

            ImGui.Text("World Generation");
            ImGui.DragInt("Seed", ref seed);
            if (ImGui.Button("Regenerate World"))
            {
                _chunkManager = new ChunkManager(
                    chunkSize: 256,
                    chunkQuality: 1024,
                    heightScale: 256f,
                    noiseSeed: seed
                );
            }

            ImGui.Text("Performance Settings");
            ImGui.SliderInt("Chunk Gen. Dist.", ref chunkRenderDistance, 1, 6);

            ImGui.Text("Display Settings");
            ImGui.SliderInt("Field of view",ref _fieldOfView,30,120);
            ImGui.SliderInt("Draw Distance", ref drawDistance, 1000, 8000);
            if (ImGui.Button("Set"))
            {
                float aspect = ClientSize.X / (float)ClientSize.Y;
                float fov = MathHelper.DegreesToRadians(_fieldOfView);
                _projection = Matrix4.CreatePerspectiveFieldOfView(fov, aspect, 0.1f, drawDistance);
            }
            System.Numerics.Vector3 lightDir = (System.Numerics.Vector3)_lightDir;
            ImGui.SliderFloat3("lightDir", ref lightDir, 0.0f,1.0f);
            _lightDir = (Vector3)lightDir;

            ImGui.End();

            // Рендерим ImGui поверх вашей игры
            _guiController.Render();



            SwapBuffers();
        }
    }
}