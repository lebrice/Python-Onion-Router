import java.io.*;
import java.net.*;

public class OnionNode2
{
	public static void main(String[] args) throws Exception
	{		
		int k2 = 5;
		
		// Port 12222 => Onion Node #2
		ServerSocket welcomeSocket = new ServerSocket(12222);
		
		while(true)
		{
			// Receive from onion node #1.
			Socket connectionSocket = welcomeSocket.accept();
			BufferedReader inFromOnionNode1 = new BufferedReader(new InputStreamReader(connectionSocket.getInputStream()));
			String receiveMessage = inFromOnionNode1.readLine();
			
			// Decrypt the middle layer of encryption.
			String decryptedMessage = "";
			for(int i = 0; i < receiveMessage.length(); i++)
			{
				decryptedMessage += (char) (receiveMessage.charAt(i) + k2);
			}
			printReceivedMessage(connectionSocket.getInetAddress(), connectionSocket.getPort(), decryptedMessage);
			
			// Send to onion node #3.
			Socket clientSocket = new Socket("localhost", 13333);
			DataOutputStream outToOnionNode3 = new DataOutputStream(clientSocket.getOutputStream());
			outToOnionNode3.writeBytes(decryptedMessage + '\n');
			
			// Receive back from onion node #3.
			BufferedReader inFromOnionNode3 = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
			String sendMessage = inFromOnionNode3.readLine();
			printReceivedMessage(clientSocket.getInetAddress(), clientSocket.getPort(), sendMessage);
			clientSocket.close();
			
			// Encrypt the middle layer of encryption.
			String encryptedMessage = "";
			for(int i = 0; i < sendMessage.length(); i++)
			{
				encryptedMessage += (char) (sendMessage.charAt(i) - k2);
			}
			
			// Send back to onion node #1.
			DataOutputStream outToOnionNode1 = new DataOutputStream(connectionSocket.getOutputStream());
			outToOnionNode1.writeBytes(encryptedMessage + '\n');
		}
	}
	
	public static void printReceivedMessage(InetAddress address, int port, String message)
	{
		System.out.println("");
		System.out.println("Onion Node #2 received a message");
		System.out.println("================================");
		System.out.println("Source IP Address:  " + address);
		System.out.println("Source Port Number: " + port);
		System.out.println("Content:            " + message);
	}
}
