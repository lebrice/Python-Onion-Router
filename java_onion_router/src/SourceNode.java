import java.io.*;
import java.net.*;

public class SourceNode
{
	public static void main(String[] args) throws Exception
	{		
		int k1 = 2;
		int k2 = 5;
		int k3 = 3;
		
		// Get the lower case message from the command line.
		BufferedReader inFromUser = new BufferedReader(new InputStreamReader(System.in));
		String message = inFromUser.readLine();
		
		// Encrypt the message with all three keys.
		String encryptedMessage = "";
		for(int i = 0; i < message.length(); i++)
		{
			encryptedMessage += (char) (message.charAt(i) - k1 - k2 - k3);
		}
		
		// Send to onion node.
		Socket clientSocket = new Socket("localhost", 11111);
		DataOutputStream outToOnionNode1 = new DataOutputStream(clientSocket.getOutputStream());
		outToOnionNode1.writeBytes(encryptedMessage + '\n');
		
		// Receive back from onion node.
		BufferedReader inFromOnionNode1 = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
		String receiveMessage = inFromOnionNode1.readLine();
		
		// Decrypt the message with all three keys.
		String decryptedMessage = "";
		for(int i = 0; i < receiveMessage.length(); i++)
		{
			decryptedMessage += (char) (receiveMessage.charAt(i) + k1 + k2 + k3);
		}
		printReceivedMessage(clientSocket.getInetAddress(), clientSocket.getPort(), decryptedMessage);
		clientSocket.close();
	}
	
	public static void printReceivedMessage(InetAddress address, int port, String message)
	{
		System.out.println("");
		System.out.println("Source Node received a message");
		System.out.println("==============================");
		System.out.println("Source IP Address:  " + address);
		System.out.println("Source Port Number: " + port);
		System.out.println("Content:            " + message);
		System.out.println("");
	}
}
