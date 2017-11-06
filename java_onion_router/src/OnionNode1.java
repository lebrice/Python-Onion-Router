import java.io.*;
import java.net.*;

public class OnionNode1
{
	public static void main(String[] args) throws Exception
	{		
		int k1 = 2;
		
		// Port 11111 => Onion Node #1
		ServerSocket welcomeSocket = new ServerSocket(11111);
		
		while(true)
		{
			// Receive from source node.
			Socket connectionSocket = welcomeSocket.accept();
			BufferedReader inFromSourceNode = new BufferedReader(new InputStreamReader(connectionSocket.getInputStream()));
			String receiveMessage = inFromSourceNode.readLine();
			
			// Decrypt the outermost layer of encryption.
			String decryptedMessage = "";
			for(int i = 0; i < receiveMessage.length(); i++)
			{
				decryptedMessage += (char) (receiveMessage.charAt(i) + k1);
			}
			printReceivedMessage(connectionSocket.getInetAddress(), connectionSocket.getPort(), decryptedMessage);
			
			// Send to destination node.
			Socket clientSocket = new Socket("localhost", 12222);
			DataOutputStream outToOnionNode2 = new DataOutputStream(clientSocket.getOutputStream());
			outToOnionNode2.writeBytes(decryptedMessage + '\n');
			
			// Receive back from destination node.
			BufferedReader inFromOnionNode2 = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
			String sendMessage = inFromOnionNode2.readLine();
			printReceivedMessage(clientSocket.getInetAddress(), clientSocket.getPort(), sendMessage);
			clientSocket.close();
			
			// Encrypt the outermost layer of encryption.
			String encryptedMessage = "";
			for(int i = 0; i < sendMessage.length(); i++)
			{
				encryptedMessage += (char) (sendMessage.charAt(i) - k1);
			}
			
			// Send back to source node.
			DataOutputStream outToSourceNode = new DataOutputStream(connectionSocket.getOutputStream());
			outToSourceNode.writeBytes(encryptedMessage + '\n');
		}
	}
	
	public static void printReceivedMessage(InetAddress address, int port, String message)
	{
		System.out.println("");
		System.out.println("Onion Node #1 received a message");
		System.out.println("================================");
		System.out.println("Source IP Address:  " + address);
		System.out.println("Source Port Number: " + port);
		System.out.println("Content:            " + message);
	}
}
