using OpenTK.Mathematics;
using System.Globalization;

namespace Mindtorio.Framework
{
    public class ObjMesh : IMeshData
    {
        public float[] Positions { get; private set; }
        public float[] Normals { get; private set; }
        public uint[] Indices { get; private set; }

        public float[] TexCoords { get; }

        public ObjMesh(string path)
        {
            var positions = new List<Vector3>();
            var normals = new List<Vector3>();

            var verts = new List<Vector3>();
            var vertNormals = new List<Vector3>();

            var indicesTemp = new List<uint>();

            using (var reader = new StreamReader(path))
            {
                string line;
                while ((line = reader.ReadLine()) != null)
                {
                    line = line.Trim();
                    if (line.StartsWith("#") || string.IsNullOrEmpty(line))
                        continue;

                    var parts = line.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
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

                        case "f":
                            // Поддержка только f v/vn/vt или v/vn или v
                            // Для простоты: f v1/vn1/vt1 v2/vn2/vt2 ...
                            var faceVerts = new List<int>();
                            var faceNorms = new List<int>();

                            for (int i = 1; i < parts.Length; i++)
                            {
                                var tokens = parts[i].Split('/');
                                int vIndex = int.Parse(tokens[0], CultureInfo.InvariantCulture) - 1;
                                faceVerts.Add(vIndex);

                                if (tokens.Length >= 3 && !string.IsNullOrEmpty(tokens[2]))
                                {
                                    int vnIndex = int.Parse(tokens[2], CultureInfo.InvariantCulture) - 1;
                                    faceNorms.Add(vnIndex);
                                }
                                else
                                {
                                    faceNorms.Add(-1);
                                }
                            }

                            // Triangulate fan (для poly > 3)
                            for (int i = 1; i < faceVerts.Count - 1; i++)
                            {
                                int i0 = faceVerts[0];
                                int i1 = faceVerts[i];
                                int i2 = faceVerts[i + 1];

                                int n0 = faceNorms[0];
                                int n1 = faceNorms[i];
                                int n2 = faceNorms[i + 1];

                                // Для каждой вершины треугольника создаём уникальную вершину (позиция + нормаль)
                                indicesTemp.Add((uint)positions.Count);
                                positions.Add(verts[i0]);
                                normals.Add(n0 >= 0 ? vertNormals[n0] : Vector3.UnitY);

                                indicesTemp.Add((uint)positions.Count);
                                positions.Add(verts[i1]);
                                normals.Add(n1 >= 0 ? vertNormals[n1] : Vector3.UnitY);

                                indicesTemp.Add((uint)positions.Count);
                                positions.Add(verts[i2]);
                                normals.Add(n2 >= 0 ? vertNormals[n2] : Vector3.UnitY);
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

            Indices = indicesTemp.ToArray();
        }
    }
}