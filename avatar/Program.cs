using AliveOnD_ID.Models;
using AliveOnD_ID.Models.Configurations;
using AliveOnD_ID.Services;
using AliveOnD_ID.Services.Interfaces;

var builder = WebApplication.CreateBuilder(args);

// load configuration from appsettings.json and environment variables
var servicesSection = builder.Configuration.GetSection("Services");

var azureSection = servicesSection.GetSection("AzureSpeechServices");
var llmSection = servicesSection.GetSection("LLM");
var didSection = servicesSection.GetSection("DID");

var didKeySetting = didSection["ApiKey"];
var asrKeySetting = azureSection["ApiKey"];
var llmKeySetting = llmSection["ApiKey"];
var llmBaseUrlSetting = llmSection["BaseUrl"];

// Substitute the D-ID API key setting with the value in the environment variable if available
if (!string.IsNullOrEmpty(didKeySetting))
{
    var didKeyValue = Environment.GetEnvironmentVariable(didKeySetting);
    if (!string.IsNullOrEmpty(didKeyValue))
    {
        builder.Configuration["Services:DID:ApiKey"] = didKeyValue;
    }
}

// Substitute the AZURE SPEECH API key setting with the value in the environment variable if available
if (!string.IsNullOrEmpty(asrKeySetting))
{
    var asrKeyValue = Environment.GetEnvironmentVariable(asrKeySetting);
    if (!string.IsNullOrEmpty(asrKeyValue))
    {
        builder.Configuration["Services:AzureSpeechServices:ApiKey"] = asrKeyValue;
    }
}

// Substitute the EVE API key setting with the value in the environment variable if available
if (!string.IsNullOrEmpty(llmKeySetting))
{
    var llmKeyValue = Environment.GetEnvironmentVariable(llmKeySetting);
    if (!string.IsNullOrEmpty(llmKeyValue))
    {
        builder.Configuration["Services:LLM:ApiKey"] = llmKeyValue;
    }
}

// Substitute the EVE Base URL setting with the value in the environment variable if available
if (!string.IsNullOrEmpty(llmBaseUrlSetting))
{
    var llmBaseUrlValue = Environment.GetEnvironmentVariable(llmBaseUrlSetting);
    if (!string.IsNullOrEmpty(llmBaseUrlValue))
    {
        builder.Configuration["Services:LLM:BaseUrl"] = llmBaseUrlValue;
    }
}

// Add MVC Controllers for API endpoints
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.Converters.Add(new System.Text.Json.Serialization.JsonStringEnumConverter());
    });

// Add Swagger/OpenAPI for testing
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo
    {
        Title = "AliveOnD-ID API",
        Version = "v1",
        Description = "API for testing AliveOnD-ID services"
    });
});
// Configure services
builder.Services.Configure<DIDConfig>(didSection);
builder.Services.Configure<AzureSpeechServicesConfig>(azureSection);
builder.Services.Configure<LLMConfig>(llmSection);
builder.Services.Configure<ServiceConfiguration>(servicesSection);

// Add application services
builder.Services.AddHttpClient();
// add memoryCache for making the StorageService work
builder.Services.AddMemoryCache();

builder.Services.AddTransient<IAvatarStreamService, AvatarStreamService>();
builder.Services.AddTransient<IASRService, ASRService>();
builder.Services.AddSingleton<ILLMService, WebSocketLLMService>();
builder.Services.AddTransient<IChatSessionService, ChatSessionService>();
builder.Services.AddTransient<IStorageService, InMemoryStorageService>();

var app = builder.Build();

// Configure the HTTP request pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseStaticFiles();

app.UseRouting();

app.UseAuthorization();

app.MapControllers();

// Map the default route to the HTML file
app.MapFallbackToFile("index.html");

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));
app.MapGet("/healthz", () => Results.Ok(new { status = "ok" }));
app.Run();
