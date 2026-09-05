#version 460 core

in vec2 TexCoord;
in vec3 FragPos;
in vec3 Normal;

out vec4 FragColor;

uniform vec3 uCameraPos;
uniform vec3 uLightDir;
uniform vec3 uLightColor;
uniform vec3 uAmbient;
uniform vec4 uWaterColor;
uniform float uTime;
uniform sampler2D uWaterTexture;

void main()
{
    vec4 texColor = texture(uWaterTexture, TexCoord * 5.0);

    vec3 waterBase = uWaterColor.rgb;

    vec3 viewDir = normalize(uCameraPos - FragPos);
    vec3 reflectDir = reflect(-normalize(uLightDir), Normal);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), 2.0);
    vec3 specular = uLightColor * spec * 0.1f;

    float diff = max(dot(Normal, normalize(uLightDir)), 0.0);
    vec3 diffuse = uLightColor * diff * 0.5f;

    vec3 finalColor = mix(waterBase, texColor.rgb, 0.3);
    vec3 result = finalColor * (uAmbient + diffuse) + specular;

    float depthFactor = 0.7f + 0.3f * sin(TexCoord.x * 10.0 + uTime) * sin(TexCoord.y * 10.0 + uTime);


    FragColor = vec4(result * depthFactor, uWaterColor.a);
}