import java.io.*;
import java.net.*;

public class OnionNode3
{
	public static void main(String[] args) throws Exception
	{
		int k3 = 3;
		
		// Port 13333 => Onion Node #3
		ServerSocket welcomeSocket = new ServerSocket(13333);
		
		while(true)
		{
			// Receive from onion node #2.
			Socket connectionSocket = welcomeSocket.accept();
			BufferedReader inFromOnionNode2 = new BufferedReader(new InputStreamReader(connectionSocket.getInputStream()));
			String receiveMessage = inFromOnionNode2.readLine();
			
			// Decrypt the innermost layer of encryption.
			String decryptedMessage = "";
			for(int i = 0; i < receiveMessage.length(); i++)
			{
				decryptedMessage += (char) (receiveMessage.charAt(i) + k3);
			}
			printReceivedMessage(connectionSocket.getInetAddress(), connectionSocket.getPort(), decryptedMessage);
			
			// Send to destination node.
			Socket clientSocket = new Socket("localhost", 14444);
			DataOutputStream outToDestinationNode = new DataOutputStream(clientSocket.getOutputStream());
			outToDestinationNode.writeBytes(decryptedMessage + '\n');
			
			// Receive back from destination node.
			BufferedReader inFromDestinationNode = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
			String sendMessage = inFromDestinationNode.readLine();
			printReceivedMessage(clientSocket.getInetAddress(), clientSocket.getPort(), sendMessage);
			clientSocket.close();
			
			// Encrypt the innermost layer of encryption.
			String encryptedMessage = "";
			for(int i = 0; i < sendMessage.length(); i++)
			{
				encryptedMessage += (char) (sendMessage.charAt(i) - k3);
			}
			
			// Send back to onion node #2.
			DataOutputStream outToOnionNode2 = new DataOutputStream(connectionSocket.getOutputStream());
			outToOnionNode2.writeBytes(encryptedMessage + '\n');
		}
	}
	
	public static void printReceivedMessage(InetAddress address, int port, String message)
	{
		System.out.println("");
		System.out.println("Onion Node #3 received a message");
		System.out.println("================================");
		System.out.println("Source IP Address:  " + address);
		System.out.println("Source Port Number: " + port);
		System.out.println("Content:            " + message);
	}
}
