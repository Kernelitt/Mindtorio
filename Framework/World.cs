using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;
using System.Runtime.Intrinsics.X86;

namespace Mindtorio.Framework;

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

    private readonly int _seed;

    private bool _isReady;

    private List<GameObject> _trees = new();
    private bool _treesCreated;

    public Chunk(int chunkX, int chunkZ, int chunkSize, int chunkQuality, float heightScale, int noiseSeed)
    {
        ChunkX = chunkX;
        ChunkZ = chunkZ;
        _seed = noiseSeed;

        Task.Run(() =>
        {
            TerrainMesh meshData = new(chunkSize, chunkSize, chunkQuality, chunkQuality, heightScale, chunkX, chunkZ, _seed);
            _pendingMesh = meshData;
            _needsGpuLoad = true;
        });
    }

    public void LoadToGpuIfReady()
    {
        if (_needsGpuLoad && _pendingMesh != null)
        {
            LoadToGpu(_pendingMesh);


            _pendingMesh = null;
            _needsGpuLoad = false;
            _isReady = true;
        }
    }

    private TerrainMesh _pendingMesh;
    private bool _needsGpuLoad;


    private void CreateTreesFromPoints(List<Vector3> spawnPoints)
    {
        if (_treesCreated || spawnPoints == null) return;

        foreach (var point in spawnPoints)
        {
            // Ствол
            var trunk = new GameObject(
                "Models/trunk.obj",
                point,
                Quaternion.Identity,
                new Vector3(0.4f, 0.25f, 0.1f),
                "Textures/Techno/Techno_06-128x128.jpg"
            )
            {
                TexScale = new Vector2(1f, 2f)
            };
            _trees.Add(trunk);

            // Листва
            var leaves = new GameObject(
                "Models/leaves.obj",
                point + new Vector3(0, 1.5f, 0),
                Quaternion.Identity,
                new Vector3(0.2f, 0.6f, 0.2f),
                "Textures/Techno/Techno_06-128x128.jpg"
            )
            {
                TexScale = new Vector2(2f, 1f)
            };
            _trees.Add(leaves);
        }

        _treesCreated = true;
    }


    private void LoadToGpu(TerrainMesh mesh)
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
        if (!_isReady) return;

        // Рендерим ландшафт
        shader.Use();
        GL.ActiveTexture(TextureUnit.Texture0);
        GL.BindTexture(TextureTarget.Texture2D, _textureId);
        GL.BindVertexArray(_vao);

        shader.SetMatrix4("uModel", Matrix4.Identity);
        shader.SetMatrix4("uView", view);
        shader.SetMatrix4("uProjection", projection);

        GL.DrawElements(PrimitiveType.Triangles, _indexCount, DrawElementsType.UnsignedInt, 0);

        GL.BindVertexArray(0);
        GL.BindTexture(TextureTarget.Texture2D, 0);

        // Рендерим деревья
        foreach (var tree in _trees)
        {
            tree.Render(shader);
        }

    }

    public void Dispose()
    {
        // Удаляем VAO
        if (_vao != 0)
        {
            GL.DeleteVertexArray(_vao);
            _vao = 0;
        }

        // Удаляем VBO
        if (_vboPos != 0)
        {
            GL.DeleteBuffer(_vboPos);
            _vboPos = 0;
        }

        if (_vboNorm != 0)
        {
            GL.DeleteBuffer(_vboNorm);
            _vboNorm = 0;
        }

        if (_vboTex != 0)
        {
            GL.DeleteBuffer(_vboTex);
            _vboTex = 0;
        }

        // Удаляем EBO
        if (_ebo != 0)
        {
            GL.DeleteBuffer(_ebo);
            _ebo = 0;
        }

        // Удаляем текстуру
        if (_textureId != 0)
        {
            GL.DeleteTexture(_textureId);
            _textureId = 0;
        }

        // Очищаем ссылки на mesh (если они ещё есть)
        _pendingMesh = null;
    }
}

public class ChunkManager(int chunkSize, int chunkQuality, float heightScale, int noiseSeed)
{
    private readonly Dictionary<(int x, int z), Chunk> _chunks = [];
    private readonly int _chunkSize = chunkSize;
    private readonly int _chunkQuality = chunkQuality;
    private readonly float _heightScale = heightScale;

    private readonly int _seed = noiseSeed;

    public void Update(Vector3 cameraPosition, int renderDistance)
    {
        int currentChunkX = (int)Math.Floor(cameraPosition.X / _chunkQuality);
        int currentChunkZ = (int)Math.Floor(cameraPosition.Z / _chunkQuality);

        // Удаляем старые чанки
        var toRemove = _chunks.Keys.Where(k =>
            Math.Abs(k.x - currentChunkX) > renderDistance ||
            Math.Abs(k.z - currentChunkZ) > renderDistance
        ).ToList();

        foreach (var key in toRemove)
        {
            ((IDisposable)_chunks[key]).Dispose();
            _chunks.Remove(key);
        }

        // Создаём новые чанки
        for (int x = currentChunkX - renderDistance; x <= currentChunkX + renderDistance; x++)
        {
            for (int z = currentChunkZ - renderDistance; z <= currentChunkZ + renderDistance; z++)
            {
                if (!_chunks.ContainsKey((x, z)))
                {
                    _chunks[(x, z)] = new Chunk(x, z, _chunkSize, _chunkQuality, _heightScale, _seed);
                }
            }
        }

        // Загружаем в GPU только чанки, которые готовы (один раз!)
        foreach (var chunk in _chunks.Values)
        {
            chunk.LoadToGpuIfReady();
        }
    }

    public void Render(Shader shader, Matrix4 view, Matrix4 projection)
    {
        foreach (var chunk in _chunks.Values)
        {
            chunk.Render(shader, view, projection);
        }
    }
    private bool _disposed;
    public void Dispose()
    {
        if (_disposed) return;

        // Dispose всех чанков
        foreach (var chunk in _chunks.Values)
        {
            chunk.Dispose();
        }

        _chunks.Clear();

        // Если есть кэш мешей — тоже очистить
        // _meshCache?.Clear();

        _disposed = true;

        GC.SuppressFinalize(this);
    }

    // Опционально: финализатор на случай если забудут вызвать Dispose
    ~ChunkManager()
    {
        Dispose();
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
    public List<Vector3> TreeSpawnPoints { get; private set; }

    private readonly PerlinNoise _noise;
    private readonly PerlinNoise _erosionNoise;
    private readonly PerlinNoise _continentalnessNoise;

    private int _seed;

    private const float GlobalMinHeight = 70f;    // Минимально возможная высота в вашем мире
    private const float GlobalMaxHeight = 650f;  // Максимально возможная высота в вашем мире
    private const float GlobalHeightRange = GlobalMaxHeight - GlobalMinHeight;

    private readonly int _chunkOffsetX;
    private readonly int _chunkOffsetZ;

    private readonly float _scaleX;
    private readonly float _scaleZ;

    private static long _totalMeshMemory = 0;
    public TerrainMesh(
        int width, int depth,
        float scaleX, float scaleZ,
        float heightScale,
        int chunkOffsetX = 0,
        int chunkOffsetZ = 0,
        int seed = 0)
    {

        _chunkOffsetX = chunkOffsetX;
        _chunkOffsetZ = chunkOffsetZ;
        _scaleX = scaleX;
        _scaleZ = scaleZ;

        

        _continentalnessNoise = new PerlinNoise(seed + 2);
        _erosionNoise =         new PerlinNoise(seed+1);
        _noise =                new PerlinNoise(seed);
        _seed = seed;

        TextureWidth = width;
        TextureHeight = depth;

        int verticesCount = width * depth;

        // Создаём сразу float[] вместо Vector3[]
        var positions = new float[verticesCount * 3];
        var normals = new float[verticesCount * 3];
        var texCoords = new float[verticesCount * 2];

        for (int z = 0; z < depth; z++)
        {
            for (int x = 0; x < width; x++)
            {
                float u = (float)x / (width - 1);
                float v = (float)z / (depth - 1);

                float worldX = u * scaleX + chunkOffsetX * scaleX;
                float worldZ = v * scaleZ + chunkOffsetZ * scaleZ;

                int idx = z * width + x;
                int posIdx = idx * 3;
                float h = GenerateHeight(worldX, worldZ, heightScale);

                positions[posIdx + 0] = worldX;
                positions[posIdx + 1] = h;
                positions[posIdx + 2] = worldZ;

                texCoords[idx * 2 + 0] = u;
                texCoords[idx * 2 + 1] = v;
            }
        }

        // Нормали теперь считают по float[] positions
        for (int z = 0; z < depth; z++)
        {
            for (int x = 0; x < width; x++)
            {
                int idx = z * width + x;
                int posIdx = idx * 3;

                float left = GetHeightAtFloat(x - 1, z, width, depth, positions);
                float right = GetHeightAtFloat(x + 1, z, width, depth, positions);
                float up = GetHeightAtFloat(x, z - 1, width, depth, positions);
                float down = GetHeightAtFloat(x, z + 1, width, depth, positions);

                float dx = right - left;
                float dz = down - up;

                // Нормализация вручную
                float len = MathF.Sqrt(dx * dx + 4f + dz * dz);
                normals[posIdx + 0] = -dx / len;
                normals[posIdx + 1] = 2f / len;
                normals[posIdx + 2] = -dz / len;
            }
        }

        Positions = positions;
        Normals = normals;
        TexCoords = texCoords;


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
        Positions = positions;
        Normals = normals;
        TexCoords = texCoords;
        Indices = indices;

        TextureRgba = GenerateTextureFromBiomes();
    
    }

    private List<Vector3> GenerateTreeSpawnPoints(float treeDensity = 0.015f, int maxTrees = 25)
    {
        var spawnPoints = new List<Vector3>();
        int totalVertices = Positions.Length / 3;
        int targetTreeCount = Math.Min((int)(totalVertices * treeDensity), maxTrees);

        // Используем детерминированный random на основе seed чанка
        var random = new Random(_seed + _chunkOffsetX * 1000 + _chunkOffsetZ);

        // Проходим только по вершинам в зоне травы (0.10 - 0.55)
        for (int idx = 0; idx < totalVertices; idx++)
        {
            if (spawnPoints.Count >= targetTreeCount)
                break;

            float y = Positions[idx * 3 + 1];
            float normalizedHeight = (y - GlobalMinHeight) / GlobalHeightRange;

            // Быстрая проверка диапазона травы
            if (normalizedHeight >= 0.10f && normalizedHeight <= 0.55f)
            {
                // Случайный выбор с нужной плотностью
                if (random.NextDouble() < treeDensity * 20)
                {
                    spawnPoints.Add(new Vector3(
                        Positions[idx * 3 + 0],
                        y,
                        Positions[idx * 3 + 2]
                    ));
                }
            }
        }

        return spawnPoints;
    }

    private static float GetHeightAtFloat(int x, int z, int width, int depth, float[] positions)
    {
        if (x < 0) x = 0;
        if (x >= width) x = width - 1;
        if (z < 0) z = 0;
        if (z >= depth) z = depth - 1;

        int idx = (z * width + x) * 3;
        return positions[idx + 1];  // Y координата
    }

    private float GenerateHeight(float x, float z, float heightScale)
    {
        float oceanMask = Smoothstep(0.4f,1f,_continentalnessNoise.Fractal(x * 0.0002f, z * 0.0002f, 24, 0.1f));


        // Эрозия — для детализации внутри гор
        float erosionHeight = MathF.Pow(
            _erosionNoise.Fractal(x * 0.0006f, z * 0.0006f, 12, 0.22f) * 1.7f,
            4f
        );


        erosionHeight = MathF.Pow(erosionHeight,1f -oceanMask);
        // Базовый шум — средняя частота для деталей гор
        float baseHeight = _noise.Fractal(
            x * 0.004f,
            z * 0.004f,
            octaves: 8,    // увеличьте с 1 до 4-6 для детализации
            persistence: 0.5f
        );
        baseHeight = Math.Clamp(baseHeight, 0f, 1f);

        float mountainHeight = MathF.Sqrt(heightScale * baseHeight) +
                              MathF.Pow(heightScale * erosionHeight, 1.1f);

        // Применяем океаническую маску и добавляем реки
        float landHeight =  mountainHeight + 300f;
        landHeight -= MathF.Pow(oceanMask,2f) * heightScale * 30; // Реки углубляются

        return landHeight;
    }

    static float Smoothstep(float edge0, float edge1, float x)
    {
        x = Math.Clamp((x - edge0) / (edge1 - edge0),0,1);
        return x * x * (3.0f - 2.0f * x);
    }


    private byte[] GenerateTextureFromBiomes()
    {
        int width = TextureWidth;
        int height = TextureHeight;
        var pixels = new byte[width * height * 4];

        Vector3 sandColor = new(0.6f, 0.5f, 0.23f);
        Vector3 grassColor = new(0.2f, 0.5f, 0.23f);
        Vector3 rockColor = new(0.58f, 0.58f, 0.6f);
        Vector3 snowColor = new(0.9f, 0.9f, 0.9f);

        for (int idx = 1; idx < Positions.Length / 3; idx++)
        { 
            float normalizedHeight = (Positions[idx * 3 + 1] - GlobalMinHeight) / GlobalHeightRange;
            normalizedHeight = Math.Clamp(normalizedHeight, 0f, 1f);

            Vector3 color;

            // Расчет плавных переходов
            if (normalizedHeight < 0.05f)
            {
                color = sandColor;
            }
            else if (normalizedHeight < 0.10f) // Песок -> Трава
            {
                float t = Smoothstep(0.05f, 0.10f, normalizedHeight);
                color = Vector3.Lerp(sandColor, grassColor, t);
            }
            else if (normalizedHeight < 0.55f)
            {
                color = grassColor;
            }
            else if (normalizedHeight < 0.85f) // Трава -> Скалы
            {
                float t = Smoothstep(0.55f, 0.85f, normalizedHeight);
                color = Vector3.Lerp(grassColor, rockColor, t);
            }
            else if (normalizedHeight < 0.95f)
            {
                color = rockColor;
            }
            else // Скалы -> Снег
            {
                float t = Smoothstep(0.95f, 0.99f, normalizedHeight);
                color = Vector3.Lerp(rockColor, snowColor, t);
            }



            int pixelIdx = idx * 4;
            pixels[pixelIdx + 0] = (byte)Math.Clamp(color.X * 255, 0, 255);
            pixels[pixelIdx + 1] = (byte)Math.Clamp(color.Y * 255, 0, 255);
            pixels[pixelIdx + 2] = (byte)Math.Clamp(color.Z * 255, 0, 255);
            pixels[pixelIdx + 3] = 255;
        }

        return pixels;
    }
}

