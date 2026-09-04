#version 460 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;

uniform float uTime;
uniform float uWaterLevel;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;

void main()
{
    vec3 pos = aPos;

    if (pos.y < uWaterLevel)
    {
        pos.y += sin(pos.x * 0.5 + uTime) * 0.1 + cos(pos.z * 0.3 + uTime) * 0.1;
    }

    gl_Position = uProjection * uView * uModel * vec4(pos, 1.0);
}