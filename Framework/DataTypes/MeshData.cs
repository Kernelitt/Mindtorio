namespace Mindtorio.Framework
{
    public interface IMeshData
    {
        float[] Positions { get; }
        float[] Normals { get; }
        uint[] Indices { get; }

        float[] TexCoords { get; } 
    }
}