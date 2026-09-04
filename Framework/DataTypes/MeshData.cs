#pragma warning disable IDE0130 // Пространство имен (namespace) не соответствует структуре папок.
namespace Mindtorio.Framework;
#pragma warning restore IDE0130 // Пространство имен (namespace) не соответствует структуре папок.

public interface IMeshData
{
    float[] Positions { get; }
    float[] Normals { get; }
    uint[] Indices { get; }

    float[] TexCoords { get; } 
}