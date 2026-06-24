import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;

public class CrowdCountingGUI extends JFrame {

    private JLabel inputImageLabel;
    private JLabel outputImageLabel;

    private JButton predictButton;

    private JTextField txtCount;

    private File selectedImage;

    public CrowdCountingGUI() {

        setTitle("Demo dự đoán mô hình");
        setSize(1000, 500);
        setLocationRelativeTo(null);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

        initUI();
    }

    private void initUI() {

        setLayout(new BorderLayout());



        //---------------------------------
        // CENTER
        //---------------------------------

        JPanel centerPanel = new JPanel();

        centerPanel.setLayout(
                new GridLayout(
                        1,
                        2,
                        50,
                        20));

        //---------------------------------
        // FRAME 1
        //---------------------------------

        JPanel leftPanel = new JPanel();

        leftPanel.setLayout(
                new BorderLayout());

        JLabel lblInput =
                new JLabel(
                        "INPUT - Chọn ảnh");

        lblInput.setFont(
                new Font("Arial",
                        Font.BOLD,
                        18));

        leftPanel.add(
                lblInput,
                BorderLayout.NORTH);

        inputImageLabel =
                new JLabel(
                        "Click để chọn ảnh",
                        SwingConstants.CENTER);

        inputImageLabel.setBorder(
                BorderFactory
                        .createLineBorder(
                                Color.BLACK));

        inputImageLabel.setPreferredSize(
                new Dimension(
                        350,
                        350));

        leftPanel.add(
                inputImageLabel,
                BorderLayout.CENTER);

        //---------------------------------
        // FRAME 2
        //---------------------------------

        JPanel rightPanel =
                new JPanel();

        rightPanel.setLayout(
                new BorderLayout());

        JLabel lblOutput =
                new JLabel(
                        "Output");

        lblOutput.setFont(
                new Font("Arial",
                        Font.BOLD,
                        18));

        rightPanel.add(
                lblOutput,
                BorderLayout.NORTH);

        outputImageLabel =
                new JLabel(
                        "Output mô hình",
                        SwingConstants.CENTER);

        outputImageLabel.setBorder(
                BorderFactory
                        .createLineBorder(
                                Color.BLACK));

        outputImageLabel.setPreferredSize(
                new Dimension(
                        350,
                        350));

        rightPanel.add(
                outputImageLabel,
                BorderLayout.CENTER);

        centerPanel.add(leftPanel);
        centerPanel.add(rightPanel);

        add(centerPanel,
                BorderLayout.CENTER);

        //---------------------------------
        // BOTTOM
        //---------------------------------

        JPanel bottomPanel =
                new JPanel();

        predictButton =
                new JButton(
                        "Dự đoán");

        predictButton.setPreferredSize(
                new Dimension(
                        150,
                        40));

        JLabel countLabel =
                new JLabel(
                        "Số người dự đoán được:");

        txtCount =
                new JTextField(10);

        txtCount.setEditable(false);

        bottomPanel.add(
                predictButton);

        bottomPanel.add(
                countLabel);

        bottomPanel.add(
                txtCount);

        add(bottomPanel,
                BorderLayout.SOUTH);

        //---------------------------------
        // SỰ KIỆN CHỌN ẢNH
        //---------------------------------

        inputImageLabel.addMouseListener(
                new MouseAdapter() {

                    @Override
                    public void mouseClicked(
                            MouseEvent e) {

                        chooseImage();
                    }
                });

        //---------------------------------
        // SỰ KIỆN DỰ ĐOÁN
        //---------------------------------

        predictButton.addActionListener(
                e -> predict());
    }

    private void chooseImage() {

        JFileChooser chooser =
                new JFileChooser();

        int result =
                chooser.showOpenDialog(this);

        if(result ==
                JFileChooser.APPROVE_OPTION){

            selectedImage =
                    chooser.getSelectedFile();

            showImage(
                    selectedImage
                            .getAbsolutePath(),
                    inputImageLabel);
        }
    }

    private void predict() {

        if(selectedImage == null){

            JOptionPane.showMessageDialog(
                    this,
                    "Vui lòng chọn ảnh!");

            return;
        }

        try {

            String result =
                    runPython(
                            selectedImage
                                    .getAbsolutePath());

            String[] data =
                    result.trim()
                            .split("\\|");

            String count =
                    data[0];

            String[] arr = count.split(" ");
            String[] arr1 = arr[arr.length -1].split("\\.");



            String outputPath =
                    data[1];

            txtCount.setText(arr1[1]);

            showImage(
                    outputPath,
                    outputImageLabel);

        }
        catch(Exception ex){

            JOptionPane.showMessageDialog(
                    this,
                    ex.getMessage());
        }
    }

    private String runPython(
            String imagePath)
            throws Exception {

        ProcessBuilder pb =
                new ProcessBuilder(
                        "python3",
                        "predict.py",
                        imagePath);

       /* ProcessBuilder pb =
                new ProcessBuilder(
                        "python3",
                        "/Users/nguyenviethuynh/Documents/Mạnh/Toán ứng dụng/predict.py",
                        imagePath);*/

        pb.redirectErrorStream(true);

        Process process =
                pb.start();

        BufferedReader reader =
                new BufferedReader(
                        new InputStreamReader(
                                process.getInputStream()));

        StringBuilder output =
                new StringBuilder();

        String line;

        while((line = reader.readLine())
                != null){

            output.append(line);
        }

        process.waitFor();

        return output.toString();
    }

    private void showImage(
            String path,
            JLabel label) {

        ImageIcon icon =
                new ImageIcon(path);

        Image img =
                icon.getImage()
                        .getScaledInstance(
                                350,
                                350,
                                Image.SCALE_SMOOTH);

        label.setIcon(
                new ImageIcon(img));

        label.setText("");
    }

    public static void main(
            String[] args) {

        SwingUtilities.invokeLater(
                () -> {

                    new CrowdCountingGUI()
                            .setVisible(true);
                });
    }
}
