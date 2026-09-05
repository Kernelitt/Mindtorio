using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;

namespace Mindtorio.Framework
{
    public class Shader
    {
        public int Handle { get; private set; }

        public Shader(string vertPath, string fragPath)
        {
            var vertSource = File.ReadAllText(vertPath);
            var fragSource = File.ReadAllText(fragPath);

            int vertShader = GL.CreateShader(ShaderType.VertexShader);
            GL.ShaderSource(vertShader, vertSource);
            GL.CompileShader(vertShader);
            CheckShaderCompile(vertShader, "Vertex");

            int fragShader = GL.CreateShader(ShaderType.FragmentShader);
            GL.ShaderSource(fragShader, fragSource);
            GL.CompileShader(fragShader);
            CheckShaderCompile(fragShader, "Fragment");

            Handle = GL.CreateProgram();
            GL.AttachShader(Handle, vertShader);
            GL.AttachShader(Handle, fragShader);
            GL.LinkProgram(Handle);

            CheckProgramLink(Handle);

            GL.DetachShader(Handle, vertShader);
            GL.DetachShader(Handle, fragShader);
            GL.DeleteShader(vertShader);
            GL.DeleteShader(fragShader);
        }

        private void CheckShaderCompile(int shader, string type)
        {
            GL.GetShader(shader, ShaderParameter.CompileStatus, out int status);
            if (status == 0)
            {
                string info = GL.GetShaderInfoLog(shader);
                throw new Exception($"{type} shader compile error:\n{info}");
            }
        }

        private void CheckProgramLink(int program)
        {
            GL.GetProgram(program, GetProgramParameterName.LinkStatus, out int status);
            if (status == 0)
            {
                string info = GL.GetProgramInfoLog(program);
                throw new Exception($"Program link error:\n{info}");
            }
        }

        public void Use()
        {
            GL.UseProgram(Handle);
        }

        public void SetMatrix4(string name, Matrix4 value)
        {
            int loc = GL.GetUniformLocation(Handle, name);
            if (loc == -1) return;
            GL.UniformMatrix4(loc, false, ref value);
        }

        public void SetVector3(string name, Vector3 value)
        {
            int loc = GL.GetUniformLocation(Handle, name);
            if (loc == -1) return;
            GL.Uniform3(loc, value);
        }

        public void SetVector4(string name, Vector4 value)
        {
            int loc = GL.GetUniformLocation(Handle, name);
            if (loc == -1) return;
            GL.Uniform4(loc, value);
        }

        public void SetInt(string name, int value)
        {
            int loc = GL.GetUniformLocation(Handle, name);
            if (loc == -1) return;
            GL.Uniform1(loc, value);
        }

        public void SetFloat(string name, float value)
        {
            int loc = GL.GetUniformLocation(Handle, name);
            if (loc == -1) return;
            GL.Uniform1(loc, value);
        }
    }
}