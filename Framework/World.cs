using OpenTK.Mathematics;
using OpenTK.Graphics.OpenGL4;
using Mindtorio.Framework;

public class Chunk : IDisposable
{
    public int ChunkX { get; }
    public int ChunkZ { get; }

    private int _vao;
    private int _vboPos;
    private int _vboNorm;
    private int _vboTex;
    private int _ebo;
    private int _textureId;

    private int _indexCount;


    public Chunk(int chunkX, int chunkZ, int chunkSize, int chunkQuality, float heightScale)
    {
        ChunkX = chunkX;
        ChunkZ = chunkZ;


        // Генерируем mesh для этого чанка
        var meshData = GenerateChunkMesh(chunkX, chunkZ, chunkSize, chunkQuality, heightScale);

        // Загружаем в OpenGL
        LoadToGpu(meshData);
    }

    private IMeshData GenerateChunkMesh(int chunkX, int chunkZ, int chunkSize, int chunkQuality, float heightScale)
    {
        // Создаём TerrainMesh для конкретного чанка
        // Смещение в мировых координатах: chunkX * chunkSize, chunkZ * chunkSize
        return new TerrainMesh(chunkSize, chunkSize, chunkQuality, chunkQuality, heightScale, chunkX, chunkZ);
    }

    private void LoadToGpu(IMeshData mesh)
    {
        _vao = GL.GenVertexArray();
        GL.BindVertexArray(_vao);

        // Позиции
        _vboPos = GL.GenBuffer();
        GL.BindBuffer(BufferTarget.ArrayBuffer, _vboPos);
        GL.BufferData(BufferTarget.ArrayBuffer, mesh.Positions.Length * sizeof(float), mesh.Positions, BufferUsageHint.StaticDraw);
        GL.VertexAttribPointer(0, 3, VertexAttribPointerType.Float, false, 3 * sizeof(float), 0);
        GL.EnableVertexAttribArray(0);

        // Нормали
        _vboNorm = GL.GenBuffer();
        GL.BindBuffer(BufferTarget.ArrayBuffer, _vboNorm);
        GL.BufferData(BufferTarget.ArrayBuffer, mesh.Normals.Length * sizeof(float), mesh.Normals, BufferUsageHint.StaticDraw);
        GL.VertexAttribPointer(1, 3, VertexAttribPointerType.Float, false, 3 * sizeof(float), 0);
        GL.EnableVertexAttribArray(1);

        // UV
        _vboTex = GL.GenBuffer();
        GL.BindBuffer(BufferTarget.ArrayBuffer, _vboTex);
        GL.BufferData(BufferTarget.ArrayBuffer, mesh.TexCoords.Length * sizeof(float), mesh.TexCoords, BufferUsageHint.StaticDraw);
        GL.VertexAttribPointer(2, 2, VertexAttribPointerType.Float, false, 2 * sizeof(float), 0);
        GL.EnableVertexAttribArray(2);

        // Индексы
        _ebo = GL.GenBuffer();
        GL.BindBuffer(BufferTarget.ElementArrayBuffer, _ebo);
        GL.BufferData(BufferTarget.ElementArrayBuffer, mesh.Indices.Length * sizeof(uint), mesh.Indices, BufferUsageHint.StaticDraw);

        // Текстура ✅
        _textureId = GL.GenTexture();
        GL.BindTexture(TextureTarget.Texture2D, _textureId);

        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMinFilter, (int)TextureMinFilter.Linear);
        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMagFilter, (int)TextureMagFilter.Linear);
        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapS, (int)TextureWrapMode.Repeat);
        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapT, (int)TextureWrapMode.Repeat);

        if (mesh is TerrainMesh tm)
        {
            GL.TexImage2D(
                TextureTarget.Texture2D,
                0,
                PixelInternalFormat.Rgba,
                tm.TextureWidth,
                tm.TextureHeight,
                0,
                PixelFormat.Rgba,
                PixelType.UnsignedByte,
                tm.TextureRgba);
        }

        GL.BindTexture(TextureTarget.Texture2D, 0);
        GL.BindVertexArray(0);

        _indexCount = mesh.Indices.Length;
    }

    public void Render(Shader shader, Matrix4 view, Matrix4 projection)
    {
        // Биндим текстуру
        GL.ActiveTexture(TextureUnit.Texture0);
        GL.BindTexture(TextureTarget.Texture2D, _textureId);

        // Биндим VAO
        GL.BindVertexArray(_vao);

        // Устанавливаем uniform'ы
        shader.SetMatrix4("uModel", Matrix4.Identity); // или смещение чанка
        shader.SetMatrix4("uView", view);
        shader.SetMatrix4("uProjection", projection);

        GL.DrawElements(PrimitiveType.Triangles, _indexCount, DrawElementsType.UnsignedInt, 0);

        // Отбіндиваем
        GL.BindVertexArray(0);

    }

    public void Dispose()
    {
        // Удаляем VAO, VBO, EBO, текстуру
    }
}

public class ChunkManager
{
    private readonly Dictionary<(int x, int z), Chunk> _chunks = new();
    private readonly int _chunkSize;
    private readonly int _chunkQuality;
    private readonly float _heightScale;


    public ChunkManager(int chunkSize, int chunkQuality, float heightScale, int noiseSeed)
    {
        _chunkSize = chunkSize;
        _chunkQuality = chunkQuality;
        _heightScale = heightScale;
    }

    public void Update(Vector3 cameraPosition, int renderDistance)
    {
        // Вычисляем, какие чанки нужны
        int currentChunkX = (int)Math.Floor(cameraPosition.X / _chunkQuality);
        int currentChunkZ = (int)Math.Floor(cameraPosition.Z / _chunkQuality);

        // Удаляем старые чанки
        var toRemove = _chunks.Keys.Where(k =>
            Math.Abs(k.x - currentChunkX) > renderDistance ||
            Math.Abs(k.z - currentChunkZ) > renderDistance
        ).ToList();

        foreach (var key in toRemove)
        {
            _chunks[key].Dispose();
            _chunks.Remove(key);
        }

        // Создаём новые чанки
        for (int x = currentChunkX - renderDistance; x <= currentChunkX + renderDistance; x++)
        {
            for (int z = currentChunkZ - renderDistance; z <= currentChunkZ + renderDistance; z++)
            {
                if (!_chunks.ContainsKey((x, z)))
                {
                    _chunks[(x, z)] = new Chunk(x, z, _chunkSize, _chunkQuality, _heightScale);
                }

            }
        }
    }

    public void Render(Shader shader, Matrix4 view, Matrix4 projection)
    {
        foreach (var chunk in _chunks.Values)
        {
            chunk.Render(shader, view, projection);
        }
    }
}

public class TerrainMesh : IMeshData
{
    public float[] Positions { get; private set; }
    public float[] Normals { get; private set; }
    public uint[] Indices { get; private set; }
    public float[] TexCoords { get; private set; }

    public int TextureWidth { get; private set; }
    public int TextureHeight { get; private set; }
    public byte[] TextureRgba { get; private set; }

    private PerlinNoise _erosionNoise;

    private PerlinNoise _continentalnessNoise;


    private PerlinNoise _noise;

    private Vector3[] _positions;
    private readonly int _chunkOffsetX;
    private readonly int _chunkOffsetZ;

    private readonly float _scaleX;
    private readonly float _scaleZ;


    public TerrainMesh(
        int width, int depth,
        float scaleX, float scaleZ,
        float heightScale,
        int chunkOffsetX = 0,
        int chunkOffsetZ = 0)
    {

        _chunkOffsetX = chunkOffsetX;
        _chunkOffsetZ = chunkOffsetZ;
        _scaleX = scaleX;
        _scaleZ = scaleZ;

        int seed = 0;

        _continentalnessNoise = new PerlinNoise(seed + 2);
        _erosionNoise =         new PerlinNoise(seed+1);
        _noise =                new PerlinNoise(seed);


        TextureWidth = width;
        TextureHeight = depth;

        int verticesCount = width * depth;


        _positions = new Vector3[verticesCount];
        var normals = new Vector3[verticesCount];
        var texCoords = new Vector2[verticesCount];

        for (int z = 0; z < depth; z++)
        {
            for (int x = 0; x < width; x++)
            {
                float u = (float)x / (width - 1);
                float v = (float)z / (depth - 1);

                float worldX = u * scaleX + chunkOffsetX * scaleX;
                float worldZ = v * scaleZ + chunkOffsetZ * scaleZ;


                int idx = z * width + x;
                float h = GenerateHeight(worldX, worldZ, heightScale);
                _positions[idx] = new Vector3(worldX, h, worldZ);
                texCoords[idx] = new Vector2(u, v);

            }
        }


        // Нормали
        for (int z = 0; z < depth; z++)
        {
            for (int x = 0; x < width; x++)
            {
                int idx = z * width + x;

                float left = GetHeightAt(x - 1, z, width, depth, _positions);
                float right = GetHeightAt(x + 1, z, width, depth, _positions);
                float up = GetHeightAt(x, z - 1, width, depth, _positions);
                float down = GetHeightAt(x, z + 1, width, depth, _positions);

                float dx = right - left;
                float dz = down - up;

                Vector3 normal = Vector3.Normalize(new Vector3(-dx, 2f, -dz));
                normals[idx] = normal;
            }
        }


        // Индексы
        int indicesCount = (width - 1) * (depth - 1) * 6;
        var indices = new uint[indicesCount];
        int i = 0;

        for (int z = 0; z < depth - 1; z++)
        {
            for (int x = 0; x < width - 1; x++)
            {
                uint topLeft = (uint)(z * width + x);
                uint topRight = (uint)(z * width + x + 1);
                uint bottomLeft = (uint)((z + 1) * width + x);
                uint bottomRight = (uint)((z + 1) * width + x + 1);

                indices[i++] = topLeft;
                indices[i++] = bottomLeft;
                indices[i++] = topRight;

                indices[i++] = topRight;
                indices[i++] = bottomLeft;
                indices[i++] = bottomRight;
            }
        }

        // Упаковка
        Positions = new float[_positions.Length * 3];
        Normals = new float[normals.Length * 3];
        TexCoords = new float[texCoords.Length * 2];

        for (int idx = 0; idx < _positions.Length; idx++)
        {
            Positions[idx * 3 + 0] = _positions[idx].X;
            Positions[idx * 3 + 1] = _positions[idx].Y;
            Positions[idx * 3 + 2] = _positions[idx].Z;

            Normals[idx * 3 + 0] = normals[idx].X;
            Normals[idx * 3 + 1] = normals[idx].Y;
            Normals[idx * 3 + 2] = normals[idx].Z;

            TexCoords[idx * 2 + 0] = texCoords[idx].X;
            TexCoords[idx * 2 + 1] = texCoords[idx].Y;
        }

        Indices = indices;


        // Генерация текстуры на основе тех же высот
        TextureRgba = GenerateTextureFromBiomes();
    }

    private float GenerateHeight(float x, float z, float heightScale)
    {
        // Базовый шум высоты
        float erosionHeight = MathF.Pow(_erosionNoise.Fractal(x * 0.001f, z * 0.001f, 12, 0.52f) * 1.5f, 6);
        float baseHeight = _noise.Fractal(x * 0.01f, z * 0.01f, 1, 0.42f);

        baseHeight = Math.Clamp(baseHeight, 0f, 1f);



        return baseHeight * heightScale * erosionHeight;
    }



    private byte[] GenerateTextureFromBiomes()
    {
        int width = TextureWidth;
        int height = TextureHeight;
        var pixels = new byte[width * height * 4];

        // Находим мин/макс высоту
        float minHeight = float.MaxValue;
        float maxHeight = float.MinValue;

        for (int idx = 0; idx < _positions.Length; idx++)
        {
            float h = _positions[idx].Y;
            if (h < minHeight) minHeight = h;
            if (h > maxHeight) maxHeight = h;
        }

        float heightRange = maxHeight - minHeight;
        if (heightRange < 0.001f) heightRange = 1f;

        for (int idx = 0; idx < _positions.Length; idx++)
        {
            float normalizedHeight = (_positions[idx].Y - minHeight) / 100;
            normalizedHeight = Math.Clamp(normalizedHeight, 0f, 1f);

            // просто 1 цвет
            Vector3 color = new Vector3(0.2f, 0.5f, 0.23f);
            switch (normalizedHeight)
            {
                case < 0.05f:
                    color = new Vector3(0.6f, 0.5f, 0.23f);
                    break;
                case < 0.6f:
                    color = new Vector3(0.2f, 0.5f, 0.23f);
                    break;
                case < 0.9f:
                    color = new Vector3(0.58f, 0.58f, 0.6f);
                    break;
                case <= 1.0f:
                    color = new Vector3(0.9f, 0.9f, 0.9f);
                    break;
            }
            

            // Детализирующий шум
            int x = idx % width;
            int z = idx / width;
            float detailNoise = _noise.Fractal(x * 2f, z * 2f, 6, 0.5f);
            float noiseFactor = 0.7f + 0.3f * detailNoise;

            int pixelIdx = idx * 4;
            pixels[pixelIdx + 0] = (byte)(color.X * noiseFactor * 255);
            pixels[pixelIdx + 1] = (byte)(color.Y * noiseFactor * 255);
            pixels[pixelIdx + 2] = (byte)(color.Z * noiseFactor * 255);
            pixels[pixelIdx + 3] = 255;
        }

        return pixels;
    }



    private static float GetHeightAt(int x, int z, int width, int depth, Vector3[] positions)
    {
        if (x < 0) x = 0;
        if (x >= width) x = width - 1;
        if (z < 0) z = 0;
        if (z >= depth) z = depth - 1;

        return positions[z * width + x].Y;
    }
}

