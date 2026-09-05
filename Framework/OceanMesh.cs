using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;

namespace Mindtorio.Framework
{
    public class OceanMesh : IDisposable
    {
        public int Vao { get; private set; }
        public int Vbo { get; private set; }
        public int Ebo { get; private set; }

        public int IndexCount { get; private set; }
        public float WaterLevel { get; set; }

        public int OceanTexture = -1;

        public OceanMesh(int width, int height, int segments)
        {
            GenerateMesh(width, height, segments);
        }

        private void GenerateMesh(int width, int height, int segments)
        {
            int vertices = (segments + 1) * (segments + 1);
            int indices = segments * segments * 6;

            var positions = new Vector3[vertices];
            var texCoords = new Vector2[vertices];
            var indexData = new uint[indices];

            // Генерация вершин плоскости
            for (int z = 0; z <= segments; z++)
            {
                for (int x = 0; x <= segments; x++)
                {
                    int idx = z * (segments + 1) + x;

                    float u = x / (float)segments;
                    float v = z / (float)segments;

                    positions[idx] = new Vector3(
                        (u - 0.5f) * width,
                        WaterLevel,
                        (v - 0.5f) * height
                    );

                    // UV для тайлинга текстур воды
                    texCoords[idx] = new Vector2(u * 10f, v * 10f);
                }
            }

            // Генерация индексов
            int i = 0;
            for (int z = 0; z < segments; z++)
            {
                for (int x = 0; x < segments; x++)
                {
                    int topLeft = z * (segments + 1) + x;
                    int topRight = topLeft + 1;
                    int bottomLeft = (z + 1) * (segments + 1) + x;
                    int bottomRight = bottomLeft + 1;

                    indexData[i++] = (uint)topLeft;
                    indexData[i++] = (uint)bottomLeft;
                    indexData[i++] = (uint)topRight;

                    indexData[i++] = (uint)topRight;
                    indexData[i++] = (uint)bottomLeft;
                    indexData[i++] = (uint)bottomRight;
                }
            }

            IndexCount = indices;

            // Создание VAO
            Vao = GL.GenVertexArray();
            GL.BindVertexArray(Vao);

            // Позиции
            Vbo = GL.GenBuffer();
            GL.BindBuffer(BufferTarget.ArrayBuffer, Vbo);
            GL.BufferData(BufferTarget.ArrayBuffer,
                positions.Length * Vector3.SizeInBytes,
                positions,
                BufferUsageHint.StaticDraw);

            GL.VertexAttribPointer(0, 3, VertexAttribPointerType.Float, false, Vector3.SizeInBytes, 0);
            GL.EnableVertexAttribArray(0);

            // UV координаты
            int vboTex = GL.GenBuffer();
            GL.BindBuffer(BufferTarget.ArrayBuffer, vboTex);
            GL.BufferData(BufferTarget.ArrayBuffer,
                texCoords.Length * Vector2.SizeInBytes,
                texCoords,
                BufferUsageHint.StaticDraw);

            GL.VertexAttribPointer(2, 2, VertexAttribPointerType.Float, false, Vector2.SizeInBytes, 0);
            GL.EnableVertexAttribArray(2);

            // Индексы
            Ebo = GL.GenBuffer();
            GL.BindBuffer(BufferTarget.ElementArrayBuffer, Ebo);
            GL.BufferData(BufferTarget.ElementArrayBuffer,
                indexData.Length * sizeof(uint),
                indexData,
                BufferUsageHint.StaticDraw);

            GL.BindBuffer(BufferTarget.ArrayBuffer, 0);
            GL.BindVertexArray(0);
        }

        public void LoadWaterTexture()
        {
            int tex = GL.GenTexture();
            GL.BindTexture(TextureTarget.Texture2D, tex);

            // Создаём простую процедурную текстуру (или загрузите из файла)
            int size = 256;
            var pixels = new byte[size * size * 4];

            // Простая синяя текстура с шумом
            var random = new Random(42);
            for (int i = 0; i < pixels.Length; i += 4)
            {
                pixels[i] = 40;     // R
                pixels[i + 1] = 80; // G
                pixels[i + 2] = (byte)(150 + random.Next(-20, 20)); // B
                pixels[i + 3] = 180; // A
            }

            GL.TexImage2D(TextureTarget.Texture2D, 0, PixelInternalFormat.Rgba,
                size, size, 0, PixelFormat.Rgba, PixelType.UnsignedByte, pixels);

            // ✅ КРИТИЧНО: Mipmaps + фильтрация
            GL.GenerateMipmap(GenerateMipmapTarget.Texture2D);
            GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMinFilter,
                (int)TextureMinFilter.LinearMipmapLinear);
            GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMagFilter,
                (int)TextureMagFilter.Linear);
            GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapS,
                (int)TextureWrapMode.Repeat);
            GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapT,
                (int)TextureWrapMode.Repeat);

            // Анизотропия
            int maxAniso = GL.GetInteger((GetPName)All.MaxTextureMaxAnisotropy);
            if (maxAniso > 0)
            {
                GL.TexParameter(TextureTarget.Texture2D,
                    (TextureParameterName)All.TextureMaxAnisotropy,
                    Math.Min(maxAniso, 16));
            }

            OceanTexture = tex;
        }

        public void UpdateWaterLevel(float level)
        {
            WaterLevel = level;
            // Можно обновить позиции вершин если нужно динамически менять уровень
        }

        public void Dispose()
        {
            if (Vao != 0) GL.DeleteVertexArray(Vao);
            if (Vbo != 0) GL.DeleteBuffer(Vbo);
            if (Ebo != 0) GL.DeleteBuffer(Ebo);
        }
    }
}