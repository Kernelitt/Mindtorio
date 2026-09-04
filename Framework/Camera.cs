using OpenTK.Mathematics;

namespace Mindtorio.Framework
{
    public class Camera
    {
        public Vector3 Position { get; set; }
        public Vector3 Front { get; private set; }
        public Vector3 Up { get; private set; }
        public Vector3 Right => Vector3.Normalize(Vector3.Cross(Front, Up));

        public float Yaw { get; set; }
        public float Pitch { get; set; }

        public float MovementSpeed { get; set; }
        public float MouseSensitivity { get; set; }

        public Camera(
            Vector3 position,
            float yaw = -90f,
            float pitch = 0f,
            float movementSpeed = 3f,
            float mouseSensitivity = 0.15f)
        {
            Position = position;
            Yaw = yaw;
            Pitch = pitch;
            MovementSpeed = movementSpeed;
            MouseSensitivity = mouseSensitivity;

            Up = Vector3.UnitY;
            UpdateFront();
        }

        public void ProcessMouseMovement(float deltaX, float deltaY)
        {
            Yaw += deltaX * MouseSensitivity;
            Pitch -= deltaY * MouseSensitivity;

            if (Pitch > 89f) Pitch = 89f;
            if (Pitch < -89f) Pitch = -89f;

            UpdateFront();
        }

        public void ProcessKeyboard(CameraMovement direction, float deltaTime)
        {
            float speed = MovementSpeed * deltaTime;

            switch (direction)
            {
                case CameraMovement.Forward:
                    Position += Front * speed;
                    break;
                case CameraMovement.Backward:
                    Position -= Front * speed;
                    break;
                case CameraMovement.Left:
                    Position -= Right * speed;
                    break;
                case CameraMovement.Right:
                    Position += Right * speed;
                    break;
                case CameraMovement.Up:
                    Position += Up * speed;
                    break;
                case CameraMovement.Down:
                    Position -= Up * speed;
                    break;
            }
        }

        public Matrix4 GetViewMatrix()
        {
            return Matrix4.LookAt(Position, Position + Front, Up);
        }

        private void UpdateFront()
        {
            float yawRad = MathHelper.DegreesToRadians(Yaw);
            float pitchRad = MathHelper.DegreesToRadians(Pitch);

            Vector3 newFront;
            newFront.X = MathF.Cos(yawRad) * MathF.Cos(pitchRad);
            newFront.Y = MathF.Sin(pitchRad);
            newFront.Z = MathF.Sin(yawRad) * MathF.Cos(pitchRad);

            Front = Vector3.Normalize(newFront);
        }
    }

    public enum CameraMovement
    {
        Forward,
        Backward,
        Left,
        Right,
        Up,
        Down
    }
}