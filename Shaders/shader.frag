#version 460 core

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

uniform sampler2D uTerrainTexture;
uniform int uUseTerrainTexture; 

uniform vec3 uCameraPos;
uniform vec3 uLightDir;
uniform vec3 uLightColor;
uniform vec3 uAmbient;
uniform vec3 uObjectColor;
uniform float uObjectReflectPower;


void main()
{
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(uLightDir);

    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diff * uLightColor;
    vec3 ambient = uAmbient * uLightColor;

    vec3 baseColor;
    if (uUseTerrainTexture == 1)
    {
        baseColor = texture(uTerrainTexture, TexCoord).rgb;
    }
    else
    {
        baseColor = uObjectColor;
    }
	
	vec3 viewdir = normalize(uCameraPos - FragPos);
	vec3 reflectdir = reflect(-lightDir, norm);
	
	vec3 specularColor = pow(max(0.0f, dot(reflectdir,viewdir)), 32) * uLightColor * uObjectReflectPower;

    vec3 result = (ambient + diffuse + specularColor) * baseColor;
    FragColor = vec4(result, 1.0);
}