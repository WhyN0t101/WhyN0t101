
package first;
import java.util.Scanner;

public class First {

    public static void main(String[] args) {
        System.out.println("First Java Project Designed By Me\n");
        System.out.println("This Project consists in being a calculator\n");
        System.out.println("Press the number correspoding to the calculus you wanna do\n");
        System.out.println("1.Sum\n2.Subtraction\n3.Multiplication\n4.Division\n");
        System.out.println("Action: ");
        Scanner num = new Scanner(System.in);
        int n = num.nextInt();
       
       if(n == 1){
                System.out.println("First Number: ");      
                float x = num.nextInt();
                System.out.println("Second Number");
                float x1 = num.nextInt();
                float y;
                y = (x+x1);
                System.out.println("The addition of those numbers is:  " + y);
       }else if(n == 2){
                 System.out.println("First Number: ");      
                float x = num.nextInt();
                System.out.println("Second Number");
                float x1 = num.nextInt();
                float y;
                y = (x-x1);
                System.out.println("The subtraction of those numbers is:  " + y);
       }else if(n ==3){
                System.out.println("First Number: ");      
                float x = num.nextInt();
                System.out.println("Second Number");
                float x1 = num.nextInt();
                float y;
                y = (x*x1);
                System.out.println("The multplication of those numbers is:  " + y);
       }else if(n == 4 ){
                 System.out.println("First Number: ");      
                float x = num.nextInt();
                System.out.println("Second Number");
                float x1 = num.nextInt();
                float y;
                float y1;
                y = (x/x1);
                y1 = (x%x1);
                System.out.println("The division of those numbers is:  " + y + " and the rest: " + y1 );
       }else {
          System.out.print("Choose a number between 1 and 4");
       }
        
        
    }
    
}
