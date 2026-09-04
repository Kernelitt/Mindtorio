using System;
using System.Runtime.InteropServices;
using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;

namespace Mindtorio.Framework
{
    internal sealed class TerrainTexture2D : IDisposable
    {
        private uint _texture;

        public TerrainTexture2D(byte[] rgbaPixels, int width, int height)
        {
            _texture = (uint)GL.GenTexture();
            Bind();

            GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMinFilter, (int)TextureMinFilter.Linear);
            GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMagFilter, (int)TextureMagFilter.Linear);
            GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapS, (int)TextureWrapMode.Repeat);
            GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapT, (int)TextureWrapMode.Repeat);

            IntPtr pixelData = Marshal.AllocHGlobal(rgbaPixels.Length);
            try
            {
                Marshal.Copy(rgbaPixels, 0, pixelData, rgbaPixels.Length);

                GL.TexImage2D(
                    TextureTarget.Texture2D,
                    0,
                    PixelInternalFormat.Rgba,
                    width,
                    height,
                    0,
                    PixelFormat.Rgba,
                    PixelType.UnsignedByte,
                    pixelData);
            }
            finally
            {
                Marshal.FreeHGlobal(pixelData);
            }

            GL.BindTexture(TextureTarget.Texture2D, 0);
        }

        public void Bind()
        {
            GL.ActiveTexture(TextureUnit.Texture0);
            GL.BindTexture(TextureTarget.Texture2D, _texture);
        }

        public void Dispose()
        {
            if (_texture != 0)
            {
                GL.DeleteTexture(_texture);
                _texture = 0;
            }
        }
    }
}