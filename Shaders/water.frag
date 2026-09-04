#version 460 core
in vec3 FragPos;
in vec3 Normal;

uniform vec3 uWaterColor;
uniform float uWaterLevel;
uniform vec3 uCameraPos;
uniform vec3 uLightDir;
uniform vec3 uLightColor;
uniform vec3 uAmbient;
uniform float uObjectReflectPower;

out vec4 FragColor;

void main()
{
    if (FragPos.y < uWaterLevel)
    {
		vec3 norm = normalize(Normal);
		vec3 lightDir = normalize(uLightDir);

		float diff = max(dot(norm, lightDir), 0.0);
		vec3 diffuse = diff * uLightColor;
		vec3 ambient = uAmbient * uLightColor;
			
		vec3 viewdir = normalize(uCameraPos - FragPos);
		vec3 reflectdir = reflect(-lightDir, norm);
		
		vec3 specularColor = pow(max(0.0f, dot(reflectdir,viewdir)), 128) * uLightColor * uObjectReflectPower;
		vec3 EndColor = (ambient + diffuse + specularColor) * uWaterColor;
        FragColor = vec4(FragColor, 0.6);
    }
    else
    {
        // Terrain
        FragColor = vec4(texture(uTerrainTexture, TexCoord).rgb, 1.0);
    }
}