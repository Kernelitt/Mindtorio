using ImGuiNET;
using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;
using OpenTK.Windowing.Common;
using OpenTK.Windowing.Desktop;
using OpenTK.Windowing.GraphicsLibraryFramework;
using System.Drawing;

namespace Mindtorio.Framework
{
    public class GLRenderer(GameWindowSettings gameWindowSettings, NativeWindowSettings nativeWindowSettings) : GameWindow(gameWindowSettings, nativeWindowSettings)
    {
        private Shader _shader;

        private Camera _camera;

        private bool _firstMove = true;
        private float _lastX;
        private float _lastY;

        private Matrix4 _projection;

        // Свет
        private Vector3 _lightDir;
        private Vector3 _lightColor;
        private Vector3 _ambient;

        private ChunkManager _chunkManager;

        private Matrix4 _lightSpaceMatrix;

        private int _fieldOfView = 60, drawDistance = 16000, chunkRenderDistance = 3;

        private bool isMouseFixed = true;

        private ImGuiController _guiController;
        private int seed = 0;

        private OceanMesh _ocean;
        private Shader _oceanShader;
        private float _renderTime = 0f;
        private Vector4 _waterColor = new(0.1f, 0.3f, 0.6f, 0.9f);

        private GameObject Player;

        private NetworkManager _networkManager;
        private string _ipInput = "127.0.0.1"; // Для ImGui буфера
        private int _portInput = 7777;


        protected override void OnLoad()
        {
            base.OnLoad();

            GL.ClearColor(0.26f, 0.28f, 0.7f, 1.0f);
            GL.Enable(EnableCap.DepthTest);

            _shader = new Shader("Shaders/shader.vert", "Shaders/shader.frag");
            _oceanShader = new Shader("Shaders/ocean.vert", "Shaders/ocean.frag");
            _ocean = new OceanMesh(width: int.MaxValue, height: int.MaxValue, segments: 64);
            _ocean.LoadWaterTexture();

            _networkManager = new NetworkManager();

            _ocean.UpdateWaterLevel(-200f);

            Player = new GameObject("Models/PlayerShip.obj", new Vector3(), new Quaternion(),
                new Vector3(1.0f, 0.2f, 0.5f), "Textures/Techno/Techno_06-128x128.jpg")
            {
                TexScale = (8f, 8f)
            };

            _chunkManager = new ChunkManager(
                chunkSize: 256,
                chunkQuality: 4096,
                heightScale: 256f,
                noiseSeed: 0
            );

            // Камера
            _camera = new Camera(
                position: new Vector3(0f, 200f, 5f),
                yaw: -90f,
                pitch: 0f,
                movementSpeed: 1000f,
                mouseSensitivity: 0.15f
            );



            float aspect = ClientSize.X / (float)ClientSize.Y;
            float fov = MathHelper.DegreesToRadians(60f);
            float near = 0.1f;
            float far = 16000f;
            _projection = Matrix4.CreatePerspectiveFieldOfView(fov, aspect, near, far);

            // Свет
            _lightDir = new Vector3(1f, 0.4f, 1f); 
            _lightColor = new Vector3(0.9f, 0.9f, 0.9f);
            _ambient = new Vector3(0.2f, 0.2f, 0.2f);

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
            float fov = MathHelper.DegreesToRadians(_fieldOfView);
            float near = 0.1f;
            _projection = Matrix4.CreatePerspectiveFieldOfView(fov, aspect, near, drawDistance);

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

            var currentPlayers = _networkManager.GetPlayersSnapshot();
            foreach (var remotePlayer in currentPlayers)
            {
                remotePlayer.Interpolate((float)e.Time);
            }

            // Отправляем позицию локального игрока в сеть
            if (_networkManager.IsConnected)
            {
                _networkManager.SendPlayerTransform(_camera.Position, _camera.Yaw);
            }

        }

        protected override void OnRenderFrame(FrameEventArgs e)
        {
            base.OnRenderFrame(e);

            GL.Viewport(0, 0, ClientSize.X, ClientSize.Y);
            GL.Clear(ClearBufferMask.ColorBufferBit | ClearBufferMask.DepthBufferBit);



            _shader.Use();
            _shader.SetVector3("uObjectColor", Vector3.One);
            _shader.SetVector3("uCameraPos", _camera.Position);
            // Привязка shadow map
            GL.ActiveTexture(TextureUnit.Texture0);
            _shader.SetMatrix4("uLightSpace", _lightSpaceMatrix);

            _shader.SetFloat("uObjectReflectPower", 0.25f); 
            _shader.SetInt("uTexture", 0); 
            _shader.SetInt("uUseTexture", 1); 

            _shader.SetMatrix4("uView", _camera.GetViewMatrix());
            _shader.SetMatrix4("uProjection", _projection);

            _shader.SetVector3("uLightDir", _lightDir);
            _shader.SetVector3("uLightColor", _lightColor);
            _shader.SetVector3("uAmbient", _ambient);
            _shader.SetVector2("uTexScale", Vector2.One);
            _shader.SetVector2("uTexOffset", Vector2.Zero);
            _chunkManager.Render(_shader, _camera.GetViewMatrix(), _projection);
            _shader.SetInt("uUseTerrainTexture", 0);


            Player.Position = _camera.Position - new Vector3(0f, 1f, 0f);
            Player.Quaternion.Y = MathHelper.DegreesToRadians(-_camera.Yaw - 90);
            Player.Render(_shader);

            foreach (var remotePlayer in _networkManager.RemotePlayers.Values)
            {
                // Временно смещаем объект игрока в координаты сетевого клона
                Player.Position = remotePlayer.Position - new Vector3(0f, 1f, 0f);
                Player.Quaternion.Y = MathHelper.DegreesToRadians(-remotePlayer.Yaw - 90);

                // Меняем цвет сетевых игроков, чтобы отличать их от себя (например, на зеленый)
                Vector3 originalColor = Player.Color;
                Player.Color = new Vector3(0.2f, 0.8f, 0.2f);

                Player.Render(_shader);

                // Возвращаем цвет обратно
                Player.Color = originalColor;
            }

            // В OnRenderFrame():
            _renderTime += (float)e.Time;

            _oceanShader.Use();
            _shader.SetVector3("uObjectColor", Vector3.One);
            _oceanShader.SetMatrix4("uModel", Matrix4.Identity);
            _oceanShader.SetMatrix4("uView", _camera.GetViewMatrix());
            _oceanShader.SetMatrix4("uProjection", _projection);
            _oceanShader.SetFloat("uTime", _renderTime);
            _oceanShader.SetVector3("uCameraPos", _camera.Position);
            _oceanShader.SetVector3("uLightDir", _lightDir);
            _oceanShader.SetVector3("uLightColor", _lightColor);
            _oceanShader.SetVector3("uAmbient", _ambient);
            _oceanShader.SetVector4("uWaterColor", _waterColor);

            GL.ActiveTexture(TextureUnit.Texture0);
            GL.BindTexture(TextureTarget.Texture2D, _ocean.OceanTexture);
            _oceanShader.SetInt("uWaterTexture", 0);

            GL.Enable(EnableCap.Blend);
            GL.BlendFunc(BlendingFactor.SrcAlpha, BlendingFactor.OneMinusSrcAlpha);

            GL.BindVertexArray(_ocean.Vao);
            GL.DrawElements(PrimitiveType.Triangles, _ocean.IndexCount, DrawElementsType.UnsignedInt, 0);
            GL.BindVertexArray(0);

            GL.Disable(EnableCap.Blend);

            // ИНТЕРФЕЙС ДЛЯ ОТЛАДКИ

            // Начинаем сборку интерфейса
            _guiController.Update(this, (float)e.Time);

            ImGui.Begin("Debug Menu");
            ImGui.SetWindowSize(new System.Numerics.Vector2(400f,330f));

            ImGui.Text("Press Esc to Lock/Release cursor");

            ImGui.Text("World Generation");
            ImGui.DragInt("Seed", ref seed);
            if (ImGui.Button("Regenerate World"))
            {
                _chunkManager.Dispose();
                _chunkManager = new ChunkManager(
                    chunkSize: 256,
                    chunkQuality: 4096,
                    heightScale: 256f,
                    noiseSeed: seed
                );
            }

            ImGui.Text("Performance Settings");
            ImGui.SliderInt("Chunk Gen. Dist.", ref chunkRenderDistance, 1, 12);

            ImGui.Text("Display Settings");
            ImGui.SliderInt("Field of view",ref _fieldOfView,30,120);
            ImGui.SliderInt("Draw Distance", ref drawDistance, 1000, 500000);
            if (ImGui.Button("Set"))
            {
                float aspect = ClientSize.X / (float)ClientSize.Y;
                float fov = MathHelper.DegreesToRadians(_fieldOfView);
                _projection = Matrix4.CreatePerspectiveFieldOfView(fov, aspect, 0.1f, drawDistance);
            }

            //Light Direction
            System.Numerics.Vector3 lightDir = (System.Numerics.Vector3)_lightDir;
            ImGui.SliderFloat3("lightDir", ref lightDir, 0.0f,1.0f);
            _lightDir = (Vector3)lightDir;

            //Player
            System.Numerics.Vector3 playerColor = (System.Numerics.Vector3)Player.Color;
            ImGui.ColorEdit3("Player Color", ref playerColor);
            Player.Color = (Vector3)playerColor;

            // Ocean
            ImGui.Text("Ocean Settings");
            var waterColorVec = new System.Numerics.Vector4(_waterColor.X, _waterColor.Y, _waterColor.Z, _waterColor.W);
            if (ImGui.ColorEdit4("Water Color", ref waterColorVec))
            {
                _waterColor = new Vector4(waterColorVec.X, waterColorVec.Y, waterColorVec.Z, waterColorVec.W);
            }

            ImGui.Separator();
            ImGui.Text("Multiplayer Settings");

            if (!_networkManager.IsConnected && !_networkManager.IsServerRunning)
            {
                ImGui.InputText("Server IP", ref _ipInput, 32);
                ImGui.InputInt("Port", ref _portInput);

                if (ImGui.Button("Host Game (Server + Client)"))
                {
                    _networkManager.StartHost((ushort)_portInput);
                }
                ImGui.SameLine();
                if (ImGui.Button("Connect to Server"))
                {
                    _networkManager.ConnectToServer(_ipInput, (ushort)_portInput);
                }
            }
            else
            {
                if (_networkManager.IsServerRunning)
                {
                    ImGui.TextColored(new System.Numerics.Vector4(0f, 1f, 0f, 1f), $"Hosting on port: {_portInput}");

                }
                else if (_networkManager.IsConnected)
                {
                    ImGui.TextColored(new System.Numerics.Vector4(0f, 1f, 0f, 1f), $"Connected to {_ipInput}:{_portInput}");
                }

                ImGui.Text($"Active Remote Players: {_networkManager.RemotePlayers.Count}");

                if (ImGui.Button("Disconnect / Stop Host"))
                {
                    _networkManager.Disconnect();
                }
                ImGui.Text("--- Network Players ---");
                var activePlayers = _networkManager.GetPlayersSnapshot();
                if (activePlayers.Count == 0)
                {
                    ImGui.Text("No remote players in dictionary.");
                }
                else
                {
                    foreach (var p in activePlayers)
                    {
                        ImGui.Text($"Player: Pos({p.Position.X:F1}, {p.Position.Y:F1}, {p.Position.Z:F1}) Yaw: {p.Yaw:F1}");
                    }
                }

            }
            ImGui.Separator();

            ImGui.End();

            // Рендерим ImGui поверх вашей игры
            _guiController.Render();



            SwapBuffers();
        }
    }
}