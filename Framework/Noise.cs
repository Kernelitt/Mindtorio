namespace Mindtorio.Framework
{
    public sealed class PerlinNoise
    {
        private readonly int[] permutation =
            new int[512];

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

            int aa = permutation[
                permutation[x0] + z0];

            int ab = permutation[
                permutation[x0] + z0 + 1];

            int ba = permutation[
                permutation[x0 + 1] + z0];

            int bb = permutation[
                permutation[x0 + 1] + z0 + 1];

            float valueA = Lerp(
                Gradient(aa, localX, localZ),
                Gradient(ab, localX, localZ - 1.0f),
                fadeZ);

            float valueB = Lerp(
                Gradient(ba, localX - 1.0f, localZ),
                Gradient(bb, localX - 1.0f, localZ - 1.0f),
                fadeZ);

            float value = Lerp(
                valueA,
                valueB,
                fadeX);

            return value * 0.5f + 0.5f;
        }

        public float Fractal(
            float x,
            float z,
            int octaves,
            float persistence)
        {
            float value = 0.0f;
            float amplitude = 1.0f;
            float frequency = 1.0f;
            float totalAmplitude = 0.0f;

            for (int i = 0; i < octaves; i++)
            {
                value += Sample(
                    x * frequency,
                    z * frequency) * amplitude;

                totalAmplitude += amplitude;

                amplitude *= persistence;
                frequency *= 2.0f;
            }

            return value / totalAmplitude;
        }

        private static float Gradient(
            int hash,
            float x,
            float z)
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
            return value * value * value *
                   (value * (value * 6.0f - 15.0f) + 10.0f);
        }

        private static float Lerp(
            float a,
            float b,
            float amount)
        {
            return a + amount * (b - a);
        }

        private static int FastFloor(float value)
        {
            int integer = (int)value;

            return value < integer
                ? integer - 1
                : integer;
        }
    }
}