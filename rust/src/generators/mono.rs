use image::{DynamicImage, Luma};
use std::path::Path;
use std::process::Command;
use std::fs;
use anyhow::{Result, anyhow};
use tempfile::NamedTempFile;

pub fn generate_grayscale_svg(img: &DynamicImage, output_path: &Path, num_tones: u32) -> Result<()> {
    if output_path.exists() {
        return Ok(());
    }

    let gray = img.to_luma8();
    let (width, height) = gray.dimensions();
    
    let mut svg_layers = Vec::new();
    let tone_levels: Vec<u8> = (0..=num_tones).map(|i| (i * 255 / num_tones) as u8).collect();

    for i in 0..num_tones as usize {
        let min_val = tone_levels[i];
        let max_val = tone_levels[i + 1];
        let tone_value = ((min_val as u16 + max_val as u16) / 2) as u8;

        if tone_value > 245 { continue; }

        let mut mask = image::ImageBuffer::new(width, height);
        let mut pixel_count = 0;
        for (x, y, p) in gray.enumerate_pixels() {
            if p.0[0] >= min_val && p.0[0] < max_val {
                mask.put_pixel(x, y, Luma([0u8])); // Black
                pixel_count += 1;
            } else {
                mask.put_pixel(x, y, Luma([255u8])); // White
            }
        }

        if pixel_count < 50 { continue; }

        let temp_bmp = NamedTempFile::new_in(".")?;
        mask.save(temp_bmp.path().with_extension("bmp"))?;
        let bmp_path = temp_bmp.path().with_extension("bmp");

        let temp_svg = NamedTempFile::new_in(".")?;
        let svg_tmp_path = temp_svg.path().with_extension("svg");

        let status = Command::new("potrace")
            .args(&[
                bmp_path.to_str().unwrap(),
                "-s",
                "-o",
                svg_tmp_path.to_str().unwrap(),
                "--flat",
                "--turdsize", "8",
                "--alphamax", "1.0",
            ])
            .status()?;

        if status.success() {
            let content = fs::read_to_string(&svg_tmp_path)?;
            let hex_color = format!("#{:02x}{:02x}{:02x}", tone_value, tone_value, tone_value);
            
            // Robustly extract the content between <svg ...> and </svg>
            if let Some(start_idx) = content.find("<svg") {
                if let Some(content_start) = content[start_idx..].find('>') {
                    let inner_content_start = start_idx + content_start + 1;
                    if let Some(end_idx) = content.rfind("</svg>") {
                        let inner_content = &content[inner_content_start..end_idx];
                        let colored_content = inner_content
                            .replace("fill=\"black\"", &format!("fill=\"{}\"", hex_color))
                            .replace("fill=\"#000000\"", &format!("fill=\"{}\"", hex_color));
                        svg_layers.push((tone_value, colored_content));
                    }
                }
            }
        }
        
        // Clean up manual bmp
        let _ = fs::remove_file(bmp_path);
        let _ = fs::remove_file(svg_tmp_path);
    }

    svg_layers.sort_by(|a, b| b.0.cmp(&a.0));

    let mut final_svg = format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n\
        <svg version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" \
        width=\"{}\" height=\"{}\" viewBox=\"0 0 {} {}\">\n",
        width, height, width, height
    );

    for (_, layer) in svg_layers {
        final_svg.push_str(&layer);
        final_svg.push('\n');
    }
    final_svg.push_str("</svg>");

    fs::write(output_path, final_svg)?;
    println!("🎨 SVG Grayscale OK: {:?}", output_path.file_name().unwrap());
    Ok(())
}

pub fn generate_halftone_svg(img: &DynamicImage, output_path: &Path) -> Result<()> {
    if output_path.exists() {
        return Ok(());
    }

    let gray = img.to_luma8();
    let (width, height) = gray.dimensions();
    let spacing = 5.0;
    let dot_size = 3.0;
    let angle = 45.0f32.to_radians();
    let cos_a = angle.cos();
    let sin_a = angle.sin();

    let mut circles = Vec::new();
    let diagonal = ((width as f32).powi(2) + (height as f32).powi(2)).sqrt() as i32;

    for y in (-diagonal..diagonal).step_by(spacing as usize) {
        for x in (-diagonal..diagonal).step_by(spacing as usize) {
            let xf = x as f32;
            let yf = y as f32;
            let orig_x = (xf * cos_a - yf * sin_a + width as f32 / 2.0) as i32;
            let orig_y = (xf * sin_a + yf * cos_a + height as f32 / 2.0) as i32;

            if orig_x >= 0 && orig_x < width as i32 && orig_y >= 0 && orig_y < height as i32 {
                let gray_val = gray.get_pixel(orig_x as u32, orig_y as u32).0[0];
                let darkness = 1.0 - (gray_val as f32 / 255.0);
                let radius = (dot_size * darkness) * 0.8;

                if radius > 0.5 {
                    circles.push(format!(
                        "<circle cx=\"{}\" cy=\"{}\" r=\"{:.2}\" fill=\"#000\" />",
                        orig_x, orig_y, radius
                    ));
                }
            }
        }
    }

    let mut svg = format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n\
        <svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{}\" height=\"{}\" viewBox=\"0 0 {} {}\">\n\
        <rect width=\"100%\" height=\"100%\" fill=\"white\"/>\n",
        width, height, width, height
    );
    for c in circles {
        svg.push_str("  ");
        svg.push_str(&c);
        svg.push('\n');
    }
    svg.push_str("</svg>");

    fs::write(output_path, svg)?;
    println!("🎨 SVG Halftone OK: {:?}", output_path.file_name().unwrap());
    Ok(())
}

pub fn generate_lineart_svg(img: &DynamicImage, output_path: &Path) -> Result<()> {
    if output_path.exists() {
        return Ok(());
    }

    let gray = img.to_luma8();
    let mut mask = image::ImageBuffer::new(gray.width(), gray.height());
    for (x, y, p) in gray.enumerate_pixels() {
        let val = if p.0[0] < 140 { 0u8 } else { 255u8 };
        mask.put_pixel(x, y, Luma([val]));
    }

    let temp_bmp = NamedTempFile::new_in(".")?;
    let bmp_path = temp_bmp.path().with_extension("bmp");
    mask.save(&bmp_path)?;

    let temp_svg = NamedTempFile::new_in(".")?;
    let svg_tmp_path = temp_svg.path().with_extension("svg");

    let status = Command::new("potrace")
        .args(&[
            bmp_path.to_str().unwrap(),
            "-s",
            "-o",
            svg_tmp_path.to_str().unwrap(),
            "--flat",
            "--turdsize", "10",
        ])
        .status()?;

    if status.success() {
        let content = fs::read_to_string(&svg_tmp_path)?;
        let mut final_svg = format!(
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n\
            <svg version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" \
            width=\"{}\" height=\"{}\" viewBox=\"0 0 {} {}\">\n",
            gray.width(), gray.height(), gray.width(), gray.height()
        );

        if let Some(start_idx) = content.find("<svg") {
            if let Some(content_start) = content[start_idx..].find('>') {
                let inner_content_start = start_idx + content_start + 1;
                if let Some(end_idx) = content.rfind("</svg>") {
                    final_svg.push_str(&content[inner_content_start..end_idx]);
                }
            }
        }
        final_svg.push_str("</svg>");
        fs::write(output_path, final_svg)?;
    }

    let _ = fs::remove_file(bmp_path);
    let _ = fs::remove_file(svg_tmp_path);

    if !status.success() {
        return Err(anyhow!("Potrace failed for lineart"));
    }

    println!("✏️ SVG Lineart OK: {:?}", output_path.file_name().unwrap());
    Ok(())
}
