uniform float     uRadius;              // set from Python (1-4 is typical)

const float w0 = 0.2270270270;      // centre
const float w1 = 0.3162162162;      // ±1.3846 px
const float w2 = 0.0702702703;      // ±3.2308 px

vec2 texelSize(float r) { return r / iResolution.xy; }

vec3 blurAxis(vec2 uv, vec2 dir, vec2 step)
{
    return texture(iChannel0, uv                      ).rgb * w0 +
           texture(iChannel0, uv + dir*1.3846*step).rgb * w1 +
           texture(iChannel0, uv - dir*1.3846*step).rgb * w1 +
           texture(iChannel0, uv + dir*3.2308*step).rgb * w2 +
           texture(iChannel0, uv - dir*3.2308*step).rgb * w2;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2  uv      = fragCoord / iResolution.xy;
    float radius  = max(uRadius, 1.0);
    vec2  stepUV  = texelSize(radius);

    vec3 blurH = blurAxis(uv, vec2(1.0, 0.0), stepUV);
    vec3 blurV = blurAxis(uv, vec2(0.0, 1.0), stepUV);

    vec3 colour = (blurH + blurV) * 0.5;
    float alpha = texture(iChannel0, uv).a;
    fragColor   = vec4(colour, alpha);
}