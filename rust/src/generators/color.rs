use image::{DynamicImage, Luma};
use std::path::Path;
use std::process::Command;
use std::fs;
use anyhow::{Result, anyhow};
use tempfile::NamedTempFile;
use kmeans_colors::get_kmeans;
use palette::{Srgb, Lab, FromColor, IntoColor};

pub fn generate_color_svg(img: &DynamicImage, output_path: &Path, num_colors: u32) -> Result<()> {
    if output_path.exists() {
        return Ok(());
    }

    let rgba = img.to_rgba8();
    let (width, height) = rgba.dimensions();
    
    // Collect visible pixels for K-means
    let mut pixels = Vec::new();
    for pixel in rgba.pixels() {
        if pixel.0[3] > 20 {
            let srgb = Srgb::new(
                pixel.0[0] as f32 / 255.0,
                pixel.0[1] as f32 / 255.0,
                pixel.0[2] as f32 / 255.0,
            );
            let lab: Lab = srgb.into_color();
            pixels.push(lab);
        }
    }

    if pixels.is_empty() {
        return Err(anyhow!("No visible pixels found for color quantization"));
    }

    let k = num_colors.min(pixels.len() as u32) as usize;
    let result = get_kmeans(k, 10, 0.005, false, &pixels, 12345);
    let colors = result.centroids;
    
    let mut svg_layers = Vec::new();

    for (i, Lab { l, a: ca, b: cb, .. }) in colors.iter().enumerate() {
        let srgb: Srgb = Srgb::from_color(Lab::new(*l, *ca, *cb));
        let r_u8 = (srgb.red * 255.0) as u8;
        let g_u8 = (srgb.green * 255.0) as u8;
        let b_u8 = (srgb.blue * 255.0) as u8;

        if r_u8 > 245 && g_u8 > 245 && b_u8 > 245 { continue; } // Skip background

        let mut mask = image::ImageBuffer::new(width, height);
        let mut found = false;
        
        for (x, y, pixel) in rgba.enumerate_pixels() {
            if pixel.0[3] > 20 {
                let px_srgb = Srgb::new(
                    pixel.0[0] as f32 / 255.0,
                    pixel.0[1] as f32 / 255.0,
                    pixel.0[2] as f32 / 255.0,
                );
                let px_lab: Lab = px_srgb.into_color();
                
                // Find nearest centroid
                let mut min_dist = f32::MAX;
                let mut best_idx = 0;
                for (idx, centroid) in colors.iter().enumerate() {
                    let d = (px_lab.l - centroid.l).powi(2) + (px_lab.a - centroid.a).powi(2) + (px_lab.b - centroid.b).powi(2);
                    if d < min_dist {
                        min_dist = d;
                        best_idx = idx;
                    }
                }

                if best_idx == i {
                    mask.put_pixel(x, y, Luma([0u8]));
                    found = true;
                } else {
                    mask.put_pixel(x, y, Luma([255u8]));
                }
            } else {
                mask.put_pixel(x, y, Luma([255u8]));
            }
        }

        if !found { continue; }

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
                "--turdsize", "2",
                "--alphamax", "0.8",
            ])
            .status()?;

        if status.success() {
            let content = fs::read_to_string(&svg_tmp_path)?;
            let hex_color = format!("#{:02x}{:02x}{:02x}", r_u8, g_u8, b_u8);
            
            // Robustly extract the content between <svg ...> and </svg>
            if let Some(start_idx) = content.find("<svg") {
                if let Some(content_start) = content[start_idx..].find('>') {
                    let inner_content_start = start_idx + content_start + 1;
                    if let Some(end_idx) = content.rfind("</svg>") {
                        let inner_content = &content[inner_content_start..end_idx];
                        // Replace common black fill values
                        let colored_content = inner_content
                            .replace("fill=\"black\"", &format!("fill=\"{}\"", hex_color))
                            .replace("fill=\"#000000\"", &format!("fill=\"{}\"", hex_color));
                        svg_layers.push(colored_content);
                    }
                }
            }
        }
        
        let _ = fs::remove_file(bmp_path);
        let _ = fs::remove_file(svg_tmp_path);
    }

    let mut final_svg = format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n\
        <svg version=\"1.1\" xmlns=\"http://www.w3.org/2000/svg\" \
        width=\"{}\" height=\"{}\" viewBox=\"0 0 {} {}\">\n",
        width, height, width, height
    );

    for layer in svg_layers {
        final_svg.push_str(&layer);
        final_svg.push('\n');
    }
    final_svg.push_str("</svg>");

    fs::write(output_path, final_svg)?;
    println!("🎨 SVG Color OK: {:?}", output_path.file_name().unwrap());
    Ok(())
}
