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

    // Ссылки на общие ресурсы (не создаём новые!)
    private readonly int _sharedVao;
    private readonly int _sharedEbo;
    private readonly int _indexCount;
    private readonly int _textureId;

    public Vector2 TexScale = Vector2.One;
    public Vector2 TexOffset = Vector2.Zero;

    public GameObject(string obj_filename, Vector3 pos, Quaternion rot, Vector3 color, string texturePath = null)
    {
        Position = pos;
        Quaternion = rot;
        Color = color;

        // Получаем из кэша (или загружаем первый раз)
        var (vao, _, _, _, ebo, indexCount) = ResourceManager.GetOrLoadMesh(obj_filename);
        _sharedVao = vao;
        _sharedEbo = ebo;
        _indexCount = indexCount;

        if (!string.IsNullOrEmpty(texturePath))
            _textureId = ResourceManager.GetOrLoadTexture(texturePath);
        else
            _textureId = -1;
    }

    public void Render(Shader _shader)
    {
        GL.BindVertexArray(_sharedVao);

        Matrix4 playerModel = Matrix4.CreateRotationX(Quaternion.X) *
                              Matrix4.CreateRotationY(Quaternion.Y) *
                              Matrix4.CreateRotationZ(Quaternion.Z) *
                              Matrix4.CreateTranslation(Position);

        _shader.SetMatrix4("uModel", playerModel);
        _shader.SetVector3("uObjectColor", Color);
        _shader.SetFloat("uObjectReflectPower", 3.0f);

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

        GL.DrawElements(PrimitiveType.Triangles, _indexCount, DrawElementsType.UnsignedInt, 0);

        if (_textureId >= 0)
            GL.BindTexture(TextureTarget.Texture2D, 0);

        GL.BindVertexArray(0);
    }
}