
using System.Drawing;
using System.Drawing.Imaging;
using OpenTK.Graphics.OpenGL4;
using PixelFormat = OpenTK.Graphics.OpenGL4.PixelFormat;
namespace Mindtorio.Framework;

public static class ResourceManager
{
    // Кэш мешей: путь к .obj -> (VAO, VBO, EBO, indexCount)
    private static readonly Dictionary<string, (int vao, int vboPos, int vboNorm, int vboTex, int ebo, int indexCount)> _meshCache = [];

    // Кэш текстур: путь -> textureId
    private static readonly Dictionary<string, int> _textureCache = [];

    public static (int vao, int vboPos, int vboNorm, int vboTex, int ebo, int indexCount) GetOrLoadMesh(string objPath)
    {
        if (_meshCache.TryGetValue(objPath, out var cached))
        {
            return cached;
        }

        var mesh = new ObjMesh(objPath);
        int vao = GL.GenVertexArray();
        GL.BindVertexArray(vao);

        int vboPos = GL.GenBuffer();
        GL.BindBuffer(BufferTarget.ArrayBuffer, vboPos);
        GL.BufferData(BufferTarget.ArrayBuffer, mesh.Positions.Length * sizeof(float), mesh.Positions, BufferUsageHint.StaticDraw);
        GL.VertexAttribPointer(0, 3, VertexAttribPointerType.Float, false, 3 * sizeof(float), 0);
        GL.EnableVertexAttribArray(0);

        int vboNorm = GL.GenBuffer();
        GL.BindBuffer(BufferTarget.ArrayBuffer, vboNorm);
        GL.BufferData(BufferTarget.ArrayBuffer, mesh.Normals.Length * sizeof(float), mesh.Normals, BufferUsageHint.StaticDraw);
        GL.VertexAttribPointer(1, 3, VertexAttribPointerType.Float, false, 3 * sizeof(float), 0);
        GL.EnableVertexAttribArray(1);

        int vboTex = GL.GenBuffer();
        GL.BindBuffer(BufferTarget.ArrayBuffer, vboTex);
        GL.BufferData(BufferTarget.ArrayBuffer, mesh.TexCoords.Length * sizeof(float), mesh.TexCoords, BufferUsageHint.StaticDraw);
        GL.VertexAttribPointer(2, 2, VertexAttribPointerType.Float, false, 2 * sizeof(float), 0);
        GL.EnableVertexAttribArray(2);

        int ebo = GL.GenBuffer();
        GL.BindBuffer(BufferTarget.ElementArrayBuffer, ebo);
        GL.BufferData(BufferTarget.ElementArrayBuffer, mesh.Indices.Length * sizeof(uint), mesh.Indices, BufferUsageHint.StaticDraw);

        GL.BindVertexArray(0);

        var result = (vao, vboPos, vboNorm, vboTex, ebo, mesh.Indices.Length);
        _meshCache[objPath] = result;
        return result;
    }

    public static int GetOrLoadTexture(string texturePath)
    {
        if (string.IsNullOrEmpty(texturePath))
            return -1;

        if (_textureCache.TryGetValue(texturePath, out int cachedTex))
        {
            return cachedTex;
        }

        int tex = GL.GenTexture();
        GL.BindTexture(TextureTarget.Texture2D, tex);

        using var bmp = new Bitmap(texturePath);
        bmp.RotateFlip(RotateFlipType.RotateNoneFlipY);

        var rect = new Rectangle(0, 0, bmp.Width, bmp.Height);
        var data = bmp.LockBits(rect, ImageLockMode.ReadOnly, System.Drawing.Imaging.PixelFormat.Format32bppArgb);

        try
        {
            GL.TexImage2D(
                TextureTarget.Texture2D,
                0,
                PixelInternalFormat.Rgba,
                bmp.Width,
                bmp.Height,
                0,
                PixelFormat.Bgra,
                PixelType.UnsignedByte,
                data.Scan0);
        }
        finally
        {
            bmp.UnlockBits(data);
        }

        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMinFilter, (int)TextureMinFilter.LinearMipmapLinear);
        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMagFilter, (int)TextureMagFilter.Linear);
        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapS, (int)TextureWrapMode.Repeat);
        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapT, (int)TextureWrapMode.Repeat);
        GL.GenerateMipmap(GenerateMipmapTarget.Texture2D);

        GL.BindTexture(TextureTarget.Texture2D, 0);

        _textureCache[texturePath] = tex;
        return tex;
    }

    public static void Cleanup()
    {
        foreach (var (vao, vboPos, vboNorm, vboTex, ebo, _) in _meshCache.Values)
        {
            GL.DeleteVertexArray(vao);
            GL.DeleteBuffer(vboPos);
            GL.DeleteBuffer(vboNorm);
            GL.DeleteBuffer(vboTex);
            GL.DeleteBuffer(ebo);
        }
        _meshCache.Clear();

        foreach (var tex in _textureCache.Values)
        {
            GL.DeleteTexture(tex);
        }
        _textureCache.Clear();
    }
}