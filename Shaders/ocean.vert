#version 460 core

layout (location = 0) in vec3 aPos;
layout (location = 2) in vec2 aTexCoord;

out vec2 TexCoord;
out vec3 FragPos;
out vec3 Normal;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;
uniform float uTime;
uniform vec3 uCameraPos;

void main()
{
    float waveAmp = 5f;
    float waveFreq1 = 0.3f;
    float waveFreq2 = 1.6f;
    float waveSpeed = 1.0f;
    
    vec3 pos = aPos;
    
    pos.y += sin(aPos.x * waveFreq1 + uTime * waveSpeed) * waveAmp;
    pos.y += sin(aPos.z * waveFreq2 + uTime * waveSpeed * 0.8f) * waveAmp * 0.5f;
    pos.y += sin((aPos.x + aPos.z) * 0.2f + uTime * waveSpeed * 1.2f) * waveAmp * 0.3f;
    
    FragPos = vec3(uModel * vec4(pos, 1.0));
    Normal = normalize(vec3(
        -cos(aPos.x * waveFreq1 + uTime * waveSpeed) * waveAmp * waveFreq1,
        1.0,
        -cos(aPos.z * waveFreq2 + uTime * waveSpeed * 0.8f) * waveAmp * waveFreq2
    ));
    
    TexCoord = aTexCoord;
    
    gl_Position = uProjection * uView * vec4(FragPos, 1.0);
}