using System.Drawing;
using System.Drawing.Imaging;
using OpenTK.Mathematics;
using OpenTK.Graphics.OpenGL4;
using PixelFormat = OpenTK.Graphics.OpenGL4.PixelFormat;

namespace Mindtorio.Framework;

internal class GameObject
{
    public Vector3 Position;
    public Quaternion Quaternion;
    public Vector3 Color;
    private ObjMesh _objMesh;
    private int _textureId;
    private int _objVao, _objVboPos, _objVboNorm, _objEbo, _objTex;

    public Vector2 TexScale = Vector2.One;     // (tilingX, tilingY)
    public Vector2 TexOffset = Vector2.Zero;

    public GameObject(string obj_filename, Vector3 pos, Quaternion rot, Vector3 color, string texturePath = null) 
    { 
        Position = pos; Quaternion = rot; Color = color;
        _objMesh = new ObjMesh(obj_filename);
        CreateMeshVao(_objMesh, out _objVao, out _objVboPos, out _objVboNorm, out _objEbo, out _objTex);

        if (!string.IsNullOrEmpty(texturePath))
            _textureId = LoadTexture(texturePath);
        else
            _textureId = -1;
    }

    private static int LoadTexture(string path)
    {
        int tex = GL.GenTexture();
        GL.BindTexture(TextureTarget.Texture2D, tex);

        using var bmp = new Bitmap(path);
        bmp.RotateFlip(RotateFlipType.RotateNoneFlipY); // OpenGL Y-up

        var rect = new Rectangle(0, 0, bmp.Width, bmp.Height);
        var data = bmp.LockBits(
            rect,
            ImageLockMode.ReadOnly,
            System.Drawing.Imaging.PixelFormat.Format32bppArgb);

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
        return tex;
    }

    private static void CreateMeshVao(ObjMesh mesh, out int vao, out int vboPos, out int vboNorm, out int ebo, out int vboTex)
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

        vboTex = GL.GenBuffer();
        GL.BindBuffer(BufferTarget.ArrayBuffer, vboTex);
        GL.BufferData(BufferTarget.ArrayBuffer, mesh.TexCoords.Length * sizeof(float), mesh.TexCoords, BufferUsageHint.StaticDraw);
        GL.VertexAttribPointer(2, 2, VertexAttribPointerType.Float, false, 2 * sizeof(float), 0);
        GL.EnableVertexAttribArray(2);

        // Индексы
        ebo = GL.GenBuffer();
        GL.BindBuffer(BufferTarget.ElementArrayBuffer, ebo);
        GL.BufferData(BufferTarget.ElementArrayBuffer, mesh.Indices.Length * sizeof(uint), mesh.Indices, BufferUsageHint.StaticDraw);

        GL.BindBuffer(BufferTarget.ArrayBuffer, 0);
        GL.BindVertexArray(0);
    }

    public void Render(Shader _shader)
    {
        GL.BindVertexArray(_objVao);

        Matrix4 playerModel = Matrix4.CreateRotationX(Quaternion.X) *
                              Matrix4.CreateRotationY(Quaternion.Y) *
                              Matrix4.CreateRotationZ(Quaternion.Z) *
                              Matrix4.CreateTranslation(Position);

        _shader.SetMatrix4("uModel", playerModel);
        _shader.SetVector3("uObjectColor", Color);
        _shader.SetFloat("uObjectReflectPower", 3.0f);

        // Текстура
        int texUnit = 0;
        _shader.SetInt("uTexture", texUnit);
        _shader.SetInt("uUseTexture", _textureId >= 0 ? 1 : 0);
        _shader.SetVector2("uTexScale", TexScale);
        _shader.SetVector2("uTexOffset", TexOffset);

        if (_textureId >= 0)
        {
            GL.ActiveTexture(TextureUnit.Texture0 + texUnit);
            GL.BindTexture(TextureTarget.Texture2D, _textureId);
        }

        GL.DrawElements(PrimitiveType.Triangles, _objMesh.Indices.Length, DrawElementsType.UnsignedInt, 0);

        if (_textureId >= 0)
            GL.BindTexture(TextureTarget.Texture2D, 0);

        GL.BindVertexArray(0);
    }
}
