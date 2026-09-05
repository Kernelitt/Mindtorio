using OpenTK.Mathematics;
using OpenTK.Graphics.OpenGL4;

namespace Mindtorio.Framework
{
    internal class GameObject
    {
        public Vector3 Position;
        public Quaternion Quaternion;
        public Vector3 Color;
        private ObjMesh _objMesh;

        private int _objVao, _objVboPos, _objVboNorm, _objEbo, _objTex;

        public GameObject(string obj_filename, Vector3 pos, Quaternion rot, Vector3 color) 
        { 
            Position = pos; Quaternion = rot; Color = color;
            _objMesh = new ObjMesh(obj_filename);
            CreateMeshVao(_objMesh, out _objVao, out _objVboPos, out _objVboNorm, out _objEbo, out _objTex);
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
            GL.DrawElements(PrimitiveType.Triangles, _objMesh.Indices.Length, DrawElementsType.UnsignedInt, 0);
            GL.BindVertexArray(0);
        }
    }
}
