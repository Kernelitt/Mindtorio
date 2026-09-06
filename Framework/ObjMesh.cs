using OpenTK.Mathematics;
using System.Globalization;

namespace Mindtorio.Framework
{
    public class ObjMesh : IMeshData
    {
        public float[] Positions { get; private set; }
        public float[] Normals { get; private set; }
        public float[] TexCoords { get; private set; }
        public uint[] Indices { get; private set; }

        public ObjMesh(string path)
        {
            var positions = new List<Vector3>();
            var normals = new List<Vector3>();
            var texCoords = new List<Vector2>();

            var verts = new List<Vector3>();
            var vertNormals = new List<Vector3>();
            var vertTex = new List<Vector2>();

            var indicesTemp = new List<uint>();

            using (var reader = new StreamReader(path))
            {
                string line;
                while ((line = reader.ReadLine()) != null)
                {
                    line = line.Trim();
                    if (line.StartsWith("#") || string.IsNullOrEmpty(line))
                        continue;

                    var parts = line.Split([' ', '\t'], StringSplitOptions.RemoveEmptyEntries);
                    if (parts.Length == 0)
                        continue;

                    switch (parts[0])
                    {
                        case "v":
                            verts.Add(new Vector3(
                                float.Parse(parts[1], CultureInfo.InvariantCulture),
                                float.Parse(parts[2], CultureInfo.InvariantCulture),
                                float.Parse(parts[3], CultureInfo.InvariantCulture)
                            ));
                            break;

                        case "vn":
                            vertNormals.Add(new Vector3(
                                float.Parse(parts[1], CultureInfo.InvariantCulture),
                                float.Parse(parts[2], CultureInfo.InvariantCulture),
                                float.Parse(parts[3], CultureInfo.InvariantCulture)
                            ));
                            break;

                        case "vt":
                            vertTex.Add(new Vector2(
                                float.Parse(parts[1], CultureInfo.InvariantCulture),
                                float.Parse(parts[2], CultureInfo.InvariantCulture)
                            ));
                            break;

                        case "f":
                            // Поддержка f v/vt/vn, v/vn, v/vt, v
                            var faceVerts = new List<int>();
                            var faceTexs = new List<int>();
                            var faceNorms = new List<int>();

                            for (int i = 1; i < parts.Length; i++)
                            {
                                var tokens = parts[i].Split('/');

                                int vIndex = int.Parse(tokens[0], CultureInfo.InvariantCulture) - 1;
                                faceVerts.Add(vIndex);

                                int vtIndex = -1;
                                if (tokens.Length >= 2 && !string.IsNullOrEmpty(tokens[1]))
                                    vtIndex = int.Parse(tokens[1], CultureInfo.InvariantCulture) - 1;
                                faceTexs.Add(vtIndex);

                                int vnIndex = -1;
                                if (tokens.Length >= 3 && !string.IsNullOrEmpty(tokens[2]))
                                    vnIndex = int.Parse(tokens[2], CultureInfo.InvariantCulture) - 1;
                                faceNorms.Add(vnIndex);
                            }

                            // Triangulate fan
                            for (int i = 1; i < faceVerts.Count - 1; i++)
                            {
                                int i0 = faceVerts[0];
                                int i1 = faceVerts[i];
                                int i2 = faceVerts[i + 1];

                                int t0 = faceTexs[0];
                                int t1 = faceTexs[i];
                                int t2 = faceTexs[i + 1];

                                int n0 = faceNorms[0];
                                int n1 = faceNorms[i];
                                int n2 = faceNorms[i + 1];

                                // Вершина 0
                                indicesTemp.Add((uint)positions.Count);
                                positions.Add(verts[i0]);
                                normals.Add(n0 >= 0 ? vertNormals[n0] : Vector3.UnitY);
                                texCoords.Add(t0 >= 0 ? vertTex[t0] : Vector2.Zero);

                                // Вершина 1
                                indicesTemp.Add((uint)positions.Count);
                                positions.Add(verts[i1]);
                                normals.Add(n1 >= 0 ? vertNormals[n1] : Vector3.UnitY);
                                texCoords.Add(t1 >= 0 ? vertTex[t1] : Vector2.Zero);

                                // Вершина 2
                                indicesTemp.Add((uint)positions.Count);
                                positions.Add(verts[i2]);
                                normals.Add(n2 >= 0 ? vertNormals[n2] : Vector3.UnitY);
                                texCoords.Add(t2 >= 0 ? vertTex[t2] : Vector2.Zero);
                            }
                            break;
                    }
                }
            }

            Positions = new float[positions.Count * 3];
            for (int i = 0; i < positions.Count; i++)
            {
                Positions[i * 3 + 0] = positions[i].X;
                Positions[i * 3 + 1] = positions[i].Y;
                Positions[i * 3 + 2] = positions[i].Z;
            }

            Normals = new float[normals.Count * 3];
            for (int i = 0; i < normals.Count; i++)
            {
                Normals[i * 3 + 0] = normals[i].X;
                Normals[i * 3 + 1] = normals[i].Y;
                Normals[i * 3 + 2] = normals[i].Z;
            }

            TexCoords = new float[texCoords.Count * 2];
            for (int i = 0; i < texCoords.Count; i++)
            {
                TexCoords[i * 2 + 0] = texCoords[i].X;
                TexCoords[i * 2 + 1] = texCoords[i].Y;
            }

            Indices = [.. indicesTemp];
        }
    }
}