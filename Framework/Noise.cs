namespace Mindtorio.Framework
{
    public sealed class PerlinNoise
    {
        private readonly int[] permutation = new int[512];
        private readonly float[] featurePointsX = new float[256];
        private readonly float[] featurePointsZ = new float[256];

        public PerlinNoise(int seed)
        {
            int[] values = new int[256];

            for (int i = 0; i < values.Length; i++)
                values[i] = i;

            Random random = new(seed);

            for (int i = 255; i > 0; i--)
            {
                int j = random.Next(i + 1);
                (values[j], values[i]) = (values[i], values[j]);
            }

            for (int i = 0; i < 512; i++)
                permutation[i] = values[i & 255];

            // Генерируем feature points для Worley шума
            for (int i = 0; i < 256; i++)
            {
                featurePointsX[i] = (float)random.NextDouble();
                featurePointsZ[i] = (float)random.NextDouble();
            }
        }

        public float Sample(float x, float z)
        {
            int cellX = FastFloor(x);
            int cellZ = FastFloor(z);

            float localX = x - cellX;
            float localZ = z - cellZ;

            float fadeX = Fade(localX);
            float fadeZ = Fade(localZ);

            int x0 = cellX & 255;
            int z0 = cellZ & 255;

            int aa = permutation[permutation[x0] + z0];
            int ab = permutation[permutation[x0] + z0 + 1];
            int ba = permutation[permutation[x0 + 1] + z0];
            int bb = permutation[permutation[x0 + 1] + z0 + 1];

            float valueA = Lerp(
                Gradient(aa, localX, localZ),
                Gradient(ab, localX, localZ - 1.0f),
                fadeZ);

            float valueB = Lerp(
                Gradient(ba, localX - 1.0f, localZ),
                Gradient(bb, localX - 1.0f, localZ - 1.0f),
                fadeZ);

            float value = Lerp(valueA, valueB, fadeX);

            return value * 0.5f + 0.5f;
        }

        public float Fractal(float x, float z, int octaves, float persistence)
        {
            float value = 0.0f;
            float amplitude = 1.0f;
            float frequency = 1.0f;
            float totalAmplitude = 0.0f;

            for (int i = 0; i < octaves; i++)
            {
                value += Sample(x * frequency, z * frequency) * amplitude;
                totalAmplitude += amplitude;
                amplitude *= persistence;
                frequency *= 2.0f;
            }

            return value / totalAmplitude;
        }

        public float WorleySmooth(float x, float z, float smoothness = 0.8f)
        {
            int cellX = FastFloor(x);
            int cellZ = FastFloor(z);

            float localX = x - cellX;
            float localZ = z - cellZ;

            float totalWeight = 0f;
            float weightedDistance = 0f;

            for (int offsetX = -1; offsetX <= 1; offsetX++)
            {
                for (int offsetZ = -1; offsetZ <= 1; offsetZ++)
                {
                    int neighborCellX = cellX + offsetX;
                    int neighborCellZ = cellZ + offsetZ;

                    int hash = Hash(neighborCellX, neighborCellZ);

                    float featureX = neighborCellX + featurePointsX[hash & 255];
                    float featureZ = neighborCellZ + featurePointsZ[hash & 255];

                    float dx = localX - (featureX - cellX);
                    float dz = localZ - (featureZ - cellZ);
                    float distance = MathF.Sqrt(dx * dx + dz * dz);

                    // Сглаживание через экспоненциальное затухание
                    float weight = MathF.Exp(-distance * smoothness);
                    weightedDistance += distance * weight;
                    totalWeight += weight;
                }
            }

            return Math.Clamp(weightedDistance / totalWeight / 1.4142f, 0f, 1f);
        }

        public float WorleyF2MinusF1(float x, float z)
        {
            int cellX = FastFloor(x);
            int cellZ = FastFloor(z);

            float localX = x - cellX;
            float localZ = z - cellZ;

            float f1 = float.MaxValue;
            float f2 = float.MaxValue;

            for (int offsetX = -1; offsetX <= 1; offsetX++)
            {
                for (int offsetZ = -1; offsetZ <= 1; offsetZ++)
                {
                    int neighborCellX = cellX + offsetX;
                    int neighborCellZ = cellZ + offsetZ;

                    int hash = Hash(neighborCellX, neighborCellZ);

                    float featureX = neighborCellX + featurePointsX[hash & 255];
                    float featureZ = neighborCellZ + featurePointsZ[hash & 255];

                    float dx = localX - (featureX - cellX);
                    float dz = localZ - (featureZ - cellZ);
                    float distance = MathF.Sqrt(dx * dx + dz * dz);

                    if (distance < f1)
                    {
                        f2 = f1;
                        f1 = distance;
                    }
                    else if (distance < f2)
                    {
                        f2 = distance;
                    }
                }
            }

            // F2-F1 даёт яркие границы
            return Math.Clamp((f2 - f1) / 1.4142f, 0f, 1f);
        }

        /// <summary>
        /// Фрактальный Worley шум для более детализированных океанов/континентов.
        /// </summary>
        public float WorleyFractal(float x, float z, int octaves, float persistence)
        {
            float value = 0.0f;
            float amplitude = 1.0f;
            float frequency = 0.5f; // Начинаем с низкой частоты для крупных форм
            float totalAmplitude = 0.0f;

            for (int i = 0; i < octaves; i++)
            {
                value += WorleySmooth(x * frequency, z * frequency) * amplitude;
                totalAmplitude += amplitude;
                amplitude *= persistence;
                frequency *= 2.0f;
            }

            return value / totalAmplitude;
        }

        private static int Hash(int x, int z)
        {
            int hash = x * 374761393 + z * 668265263;
            hash = (hash ^ 61) ^ (hash >> 16);
            hash += hash << 3;
            hash ^= hash >> 4;
            hash *= 0x27d4eb2d;
            hash ^= hash >> 15;
            return hash & 255;
        }

        private static float Gradient(int hash, float x, float z)
        {
            return (hash & 3) switch
            {
                0 => x + z,
                1 => -x + z,
                2 => x - z,
                _ => -x - z,
            };
        }

        private static float Fade(float value)
        {
            return value * value * value * (value * (value * 6.0f - 15.0f) + 10.0f);
        }

        private static float Lerp(float a, float b, float amount)
        {
            return a + amount * (b - a);
        }

        private static int FastFloor(float value)
        {
            int integer = (int)value;
            return value < integer ? integer - 1 : integer;
        }
    }
}