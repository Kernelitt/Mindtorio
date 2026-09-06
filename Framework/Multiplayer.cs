using System;
using System.Collections.Generic;
using OpenTK.Mathematics;
using Riptide;
using Riptide.Utils;

namespace Mindtorio.Framework;

    public enum MessageId : ushort
    {
        WelcomeData = 1,     // Отправка сида мира при подключении
        PlayerTransform = 2  // Синхронизация позиции и поворота
    }

    public class RemotePlayer
    {
        public Vector3 Position { get; set; }
        public Vector3 TargetPosition { get; set; }
        public float Yaw { get; set; }

        public RemotePlayer(Vector3 startPos, float yaw)
        {
            Position = startPos;
            TargetPosition = startPos;
            Yaw = yaw;
        }

        public void Interpolate(float deltaTime)
        {
            Position = Vector3.Lerp(Position, TargetPosition, deltaTime * 15f);
        }
    }
public class NetworkManager
{
    public Server Server { get; private set; }
    public Client Client { get; private set; }

    public bool IsServerRunning => Server?.IsRunning ?? false;
    public bool IsConnected => Client?.IsConnected ?? false;

    public Dictionary<ushort, RemotePlayer> RemotePlayers { get; } = new();

    public Action<int> OnSeedReceived;

    private CancellationTokenSource _cts;
    private readonly object _lock = new();
    private int _currentWorldSeed = 0;

    public NetworkManager()
    {
        Server = new Server();
        Client = new Client();

        // КРИТИЧЕСКИ ВАЖНО: Подписываемся на ВСЕ события строго в конструкторе,
        // ОДИН РАЗ и до того, как будут вызваны методы Start() или Connect().

        // Серверные события
        Server.MessageReceived += OnMessageReceivedOnServer;
        Server.ClientConnected += OnClientConnectedToServer;
        Server.ClientDisconnected += OnClientDisconnectedFromServer;

        // Клиентские события
        Client.MessageReceived += OnMessageReceivedOnClient;
        Client.Disconnected += OnDisconnectedFromServer;

        // Используем явные события Riptide для отслеживания игроков
        Client.ClientConnected += OnAnotherClientConnected;
        Client.ClientDisconnected += OnAnotherClientDisconnected;
    }

    public void StartHost(int worldSeed, ushort port = 7777)
    {
        Disconnect();
        _currentWorldSeed = worldSeed;
        _cts = new CancellationTokenSource();

        try
        {
            // Запускаем сервер синхронно в главном вызове, чтобы сокет открылся мгновенно
            Server.Start(port, 4);
            Console.WriteLine($"(SERVER): Server running on port {port}");

            // Клиент подключается
            Client.Connect($"127.0.0.1:{port}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"(NETWORK ERROR): {ex.Message}");
        }

        // Фоновый поток только крутит метод Update()
        Task.Run(() => NetworkLoopAsync(_cts.Token));
    }

    public void ConnectToServer(string ip, ushort port = 7777)
    {
        Disconnect();
        _cts = new CancellationTokenSource();

        try
        {
            Client.Connect($"{ip}:{port}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"(NETWORK ERROR): {ex.Message}");
        }

        Task.Run(() => NetworkLoopAsync(_cts.Token));
    }

    public void Disconnect()
    {
        _cts?.Cancel();
        if (Client.IsConnected) Client.Disconnect();
        if (Server.IsRunning) Server.Stop();

        lock (_lock)
        {
            RemotePlayers.Clear();
        }
    }

    private async Task NetworkLoopAsync(CancellationToken token)
    {
        while (!token.IsCancellationRequested)
        {
            // Постоянно даем Riptide обрабатывать входящую очередь пакетов
            if (Server.IsRunning) Server.Update();
            if (Client.IsConnected) Client.Update();
            if (Client.IsConnecting) Client.Update();

            await Task.Delay(10, token).ConfigureAwait(false);
        }
    }

    public void SendPlayerTransform(Vector3 position, float yaw)
    {
        // Не отправляем данные, пока сервер не выдал нам ID (он должен быть > 0)
        if (!Client.IsConnected || Client.Id == 0) return;

        Message message = Message.Create(MessageSendMode.Unreliable, (ushort)MessageId.PlayerTransform);

        // Явно приводим к float, чтобы исключить любые проблемы с double/float в OpenTK
        message.AddFloat((float)position.X);
        message.AddFloat((float)position.Y);
        message.AddFloat((float)position.Z);
        message.AddFloat((float)yaw);

        Client.Send(message);
    }


    // ==================== СЕРВЕР ====================

    private void OnClientConnectedToServer(object sender, ServerConnectedEventArgs e)
    {
        Console.WriteLine($"(SERVER): Client {e.Client.Id} connected. Sending world seed {_currentWorldSeed}");

        Message message = Message.Create(MessageSendMode.Reliable, (ushort)MessageId.WelcomeData);
        message.AddInt(_currentWorldSeed);
        Server.Send(message, e.Client.Id);
    }

    private void OnClientDisconnectedFromServer(object sender, ServerDisconnectedEventArgs e)
    {
        Console.WriteLine($"(SERVER): Client {e.Client.Id} disconnected.");
    }

    private void OnMessageReceivedOnServer(object sender, MessageReceivedEventArgs e)
    {
        if (e.MessageId == (ushort)MessageId.PlayerTransform)
        {
            try
            {
                // 1. Читаем данные, которые прислал клиент
                float x = e.Message.GetFloat();
                float y = e.Message.GetFloat();
                float z = e.Message.GetFloat();
                float yaw = e.Message.GetFloat();

                // 2. Создаем пакет для РАССЫЛКИ остальным
                Message forwardMessage = Message.Create(MessageSendMode.Unreliable, (ushort)MessageId.PlayerTransform);

                // Сначала пишем ID отправителя, ЧТОБЫ КЛИЕНТЫ ЗНАЛИ КТО ЭТО
                forwardMessage.AddUShort(e.FromConnection.Id);

                // Затем пишем его координаты
                forwardMessage.AddFloat(x);
                forwardMessage.AddFloat(y);
                forwardMessage.AddFloat(z);
                forwardMessage.AddFloat(yaw);

                // Рассылаем всем, кроме самого отправителя
                Server.SendToAll(forwardMessage, e.FromConnection.Id);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"(SERVER ERROR): Ошибка обработки трансформ-пакета: {ex.Message}");
            }
        }
    }

    // ==================== КЛИЕНТ ====================

    private void OnAnotherClientConnected(object sender, ClientConnectedEventArgs e)
    {
        // Проверяем, что это не наш собственный ID локального клиента
        if (Client.IsConnected && e.Id == Client.Id) return;

        lock (_lock)
        {
            if (!RemotePlayers.ContainsKey(e.Id))
            {
                RemotePlayers[e.Id] = new RemotePlayer(Vector3.Zero, 0f);
                Console.WriteLine($"(LOCAL CLIENT): Created RemotePlayer instance for Client ID: {e.Id}");
            }
        }
    }

    private void OnMessageReceivedOnClient(object sender, MessageReceivedEventArgs e)
    {
        if (e.MessageId == (ushort)MessageId.WelcomeData)
        {
            try
            {
                int receivedSeed = e.Message.GetInt();
                Console.WriteLine($"(LOCAL CLIENT): Получен сид мира от сервера: {receivedSeed}");
                OnSeedReceived?.Invoke(receivedSeed);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"(CLIENT ERROR): Ошибка чтения сида: {ex.Message}");
            }
        }
        else if (e.MessageId == (ushort)MessageId.PlayerTransform)
        {
            try
            {
                // Читаем строго в том порядке, в каком сервер упаковал в SendToAll:
                ushort playerId = e.Message.GetUShort(); // 1. ID игрока
                float x = e.Message.GetFloat();          // 2. X
                float y = e.Message.GetFloat();          // 3. Y
                float z = e.Message.GetFloat();          // 4. Z
                float yaw = e.Message.GetFloat();        // 5. Поворот

                // Если сервер прислал нам наши же координаты (хотя SendToAll должен это фильтровать), игнорируем
                if (Client.IsConnected && playerId == Client.Id) return;

                var receivedPos = new Vector3(x, y, z);

                lock (_lock)
                {
                    if (RemotePlayers.TryGetValue(playerId, out var player))
                    {
                        player.TargetPosition = receivedPos;
                        player.Yaw = yaw;
                    }
                    else
                    {
                        // Если событие ClientConnected не успело сработать, создаем здесь с правильной позицией!
                        player = new RemotePlayer(receivedPos, yaw);
                        RemotePlayers[playerId] = player;
                        Console.WriteLine($"(LOCAL CLIENT): Игрок {playerId} добавлен в список по сетевому пакету. Координаты: {x:F1}, {y:F1}, {z:F1}");
                    }
                }
            }
            catch (Exception ex)
            {
                // Если была ошибка несоответствия типов (разное количество байт), мы сразу увидим это в консоли
                Console.WriteLine($"(CLIENT ERROR): Ошибка чтения трансформ-пакета: {ex.Message}");
            }
        }
    }

    private void OnAnotherClientDisconnected(object sender, ClientDisconnectedEventArgs e)
    {
        lock (_lock)
        {
            if (RemotePlayers.Remove(e.Id))
            {
                Console.WriteLine($"(LOCAL CLIENT): Removed RemotePlayer ID: {e.Id}");
            }
        }
    }

    private void OnDisconnectedFromServer(object sender, DisconnectedEventArgs e)
    {
        lock (_lock)
        {
            RemotePlayers.Clear();
            Console.WriteLine("(LOCAL CLIENT): Disconnected from server. Remote players cleared.");
        }
    }

    public List<RemotePlayer> GetPlayersSnapshot()
    {
        lock (_lock)
        {
            return new List<RemotePlayer>(RemotePlayers.Values);
        }
    }
}
